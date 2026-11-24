"""One time: gives every branch that has no payment method the default ones.

Branches made from now on get them when they are made (web/management/branches/service.py); this is only for branches that already exist
without any. It writes rows, so it is run by hand and not through scripts/pra_deploy.py, whose guard refuses a deploy that changes a row count.

    python scripts/seed_payment_methods.py          # shows which branches would be filled
    python scripts/seed_payment_methods.py --tulis  # fills them
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.core.finance.payment_methods import seed_defaults  # noqa: E402
from app.models.outlet import Outlet  # noqa: E402
from app.models.payment_method import PaymentMethod  # noqa: E402


def main() -> int:
    write = "--tulis" in sys.argv[1:]
    with SessionLocal() as db:
        have = set(db.scalars(select(PaymentMethod.outlet_id).distinct()).all())
        missing = [outlet for outlet in db.scalars(select(Outlet).order_by(Outlet.name)).all() if outlet.id not in have]
        for outlet in missing:
            print(f"{'ISI' if write else 'AKAN DIISI'}: {outlet.name} ({outlet.id})")
            if write:
                seed_defaults(db, outlet.id)
        if write:
            db.commit()
        print(f"{len(missing)} cabang tanpa metode bayar." + ("" if write else " Jalankan dengan --tulis untuk mengisinya."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
