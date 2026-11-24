from fastapi import APIRouter, Depends

from app.core.auth import current_user
from app.models.user import User
from web.management.screens.registry import abilities_of, screens_of
from web.management.screens.schemas import ScreensOut

router = APIRouter(prefix="/screens", tags=["web-screens"])


# Never cached: it follows the account's role, is worked out in memory, and must change the moment a role does.
@router.get("", response_model=ScreensOut)
def my_screens(user: User = Depends(current_user)):
    """The screens this account may open and the parts inside them it may use, for the sidebar, every link, and every guarded part."""
    return ScreensOut(screens=screens_of(user), abilities=abilities_of(user))
