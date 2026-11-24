"""Server-sent events for the app: which tables changed, so an open screen reloads only what it shows."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core import live
from app.core.auth import current_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter(prefix="/live", tags=["v2-live"])


@router.get("")
async def stream(user: User = Depends(current_user), db: Session = Depends(get_db)):
    outlet_id = user.locked_outlet_id
    db.close()
    return live.stream_response(live.changes(outlet_id))
