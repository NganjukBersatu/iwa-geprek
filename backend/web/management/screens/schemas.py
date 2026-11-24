from pydantic import BaseModel

from web.management.screens.registry import Ability, Screen


class ScreensOut(BaseModel):
    screens: list[Screen]
    abilities: list[Ability]
