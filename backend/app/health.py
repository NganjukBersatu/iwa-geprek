"""Health probe used by the Railway healthcheck; it fails when the database is unreachable."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db

UNAVAILABLE = 503
STATUS_OK = "ok"

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(UNAVAILABLE, "database unreachable") from error
    return {"status": STATUS_OK}
