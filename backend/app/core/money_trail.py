"""Who changed money: the v2 account is put on the database connection per request, and the money_changes triggers read it."""
from typing import Any

from sqlalchemy import Engine, event, func, select
from sqlalchemy.orm import Session

SETTING = "app.user_id"


def act_as(db: Session, user_id: str) -> None:
    """Kept on the connection, not the transaction, so every commit of the request carries it; cleared when the connection goes back to the pool."""
    db.execute(select(func.set_config(SETTING, user_id, False)))


def _forget(dbapi_connection: Any, record: Any) -> None:
    # A connection that cannot be cleared is thrown away, so no later request can act under the previous account.
    try:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute(f"SELECT set_config('{SETTING}', '', false)")
        finally:
            cursor.close()
        dbapi_connection.commit()
    except Exception as error:
        record.invalidate(error)


def install(engine: Engine) -> None:
    event.listen(engine, "checkin", _forget)
