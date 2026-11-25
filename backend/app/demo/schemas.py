from typing import Literal

from pydantic import BaseModel


class DemoStatusOut(BaseModel):
    # False when the switch is turned off on this server or there is no demo snapshot; the sign-in page then hides the button.
    available: bool
    active: bool
    stage: Literal["idle", "preparing", "loading", "linking", "ready", "failed"]
    percent: int
    error_code: str | None
