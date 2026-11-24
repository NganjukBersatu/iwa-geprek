"""Deploy guard of v2: run the migrations in ONE transaction, check, then commit.

    python scripts/pra_deploy.py           # deploy: saved only when it passes
    python scripts/pra_deploy.py --coba     # rehearsal: ALWAYS rolled back

Steps:
  1. Snapshot row counts and money sums (read only).
  2. `alembic upgrade head` inside one transaction (Postgres DDL is transactional).
  3. Check the result: no row or sum lost or changed (app/core/migration_check.py).
  4. Pass -> commit (except --coba: rollback). Fail -> rollback, database stays as it was, exit code 1.

Set as the `preDeploy` command of the backend service in `.railway/railway.ts`. When this script exits non-zero Railway stops the deploy and the old version keeps serving.

Other safeguards:
  * lock_timeout of 30 seconds: when a table is locked by another process the migration gives up (rollback) instead of hanging.
  * Any failure, including an error in the middle of a migration -> rollback.

Do NOT use --coba directly on the production database: while the transaction is open the changed tables are locked. Use a copy of the data.
"""
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from alembic.runtime.migration import MigrationContext  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.migration_check import check, snapshot  # noqa: E402
from app.core.settings import settings  # noqa: E402

LOCK_TIMEOUT = "30s"
VERSION_TABLE = "alembic_version_v2"


def say(message: str) -> None:
    print(f"[pra-deploy {datetime.now():%H:%M:%S}] {message}", flush=True)


def main() -> int:
    rehearsal = "--coba" in sys.argv[1:]
    say("REHEARSAL MODE (--coba): the result will be rolled back." if rehearsal else "DEPLOY MODE: saved only when it passes.")

    url = make_url(settings.database_url)
    say(f"Database: {url.host}:{url.port}/{url.database}")

    cfg = Config(str(ROOT / "alembic.ini"))
    heads = ScriptDirectory.from_config(cfg).get_heads()
    if len(heads) != 1:
        say(f"FAILED: {len(heads)} migration heads ({', '.join(heads)}). Merge them first. Nothing changed.")
        return 1
    head = heads[0]

    engine = create_engine(url)
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'"))

            # The legacy app keeps serving during pre-deploy; a session idle inside a transaction holds read locks on the tables it
            # touched and makes ALTER TABLE hit the lock timeout. It is only waiting (not writing) and the app reconnects by itself.
            cut = conn.execute(
                text(
                    "SELECT count(pg_terminate_backend(pid)) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND pid <> pg_backend_pid() "
                    "AND state = 'idle in transaction' "
                    "AND now() - state_change > interval '5 seconds'"
                )
            ).scalar()
            if cut:
                say(f"Cut {cut} sessions hanging inside a transaction (holding table locks).")

            current = MigrationContext.configure(conn, opts={"version_table": VERSION_TABLE}).get_current_revision()
            say(f"Database revision: {current or '(empty)'} | code revision (head): {head}")
            if current == head:
                say("Database is already at head. No migration was run.")
                trans.rollback()
                return 0

            say("Snapshotting the state before the migration...")
            before = snapshot(conn)
            say(f"  {len(before['rows'])} tables, {sum(before['rows'].values())} rows.")

            say("Running migrations (inside a transaction, not saved yet)...")
            started = time.monotonic()
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")
            say(f"Migrations finished in {time.monotonic() - started:.1f} seconds. Checking the result...")

            problems, notes = check(conn, before)
            for note in notes:
                say(f"  note   : {note}")
            for problem in problems:
                say(f"  PROBLEM: {problem}")

            if problems:
                trans.rollback()
                say(f"FAILED: {len(problems)} problems. ROLLED BACK, database unchanged.")
                return 1
            if rehearsal:
                trans.rollback()
                say("PASSED (--coba mode): all checks safe. Rolled back, nothing saved.")
                return 0

            trans.commit()
            say(f"PASSED. Changes SAVED. Database is now at revision {head}.")
            return 0
        except BaseException:
            if trans.is_active:
                trans.rollback()
            say("FAILED: error during migration. ROLLED BACK, database unchanged.")
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    sys.exit(main())
