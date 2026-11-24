"""Server-sent events: tells an open management screen which tables changed, so it reloads only what it shows."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import live
from app.core.auth import current_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/live", tags=["web-live"])


@router.get("")
async def stream(user: User = Depends(current_user), db: Session = Depends(get_db)):
    outlet_id = user.locked_outlet_id
    # The stream stays open for hours; the connection it borrowed to sign the person in goes back to the pool at once.
    db.close()
    return live.stream_response(live.changes(outlet_id))
