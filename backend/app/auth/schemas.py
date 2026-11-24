from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

MAX_CREDENTIAL_LENGTH = 128


class LoginIn(BaseModel):
    # Spasi di awal atau akhir nama pengguna dibuang, karena nama pengguna tidak pernah memuatnya.
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_CREDENTIAL_LENGTH)]
    password: str = Field(min_length=1, max_length=MAX_CREDENTIAL_LENGTH)


class AuthUserOut(BaseModel):
    id: str
    name: str | None
    username: str
    # Kosong bila perannya dilepas (peran dihapus dari backend lama), supaya akun itu tetap bisa membuka profilnya.
    role_id: str | None
    role_name: str
    # Empty when full_access is set, since such a role holds every permission; the screen only hides what cannot be used.
    permissions: list[str]
    full_access: bool
    # Whether the management web opens for this account, decided by the server so no screen spells out the permission key.
    web_access: bool
    outlet_id: str | None
    # Stasiun dari peran akun, dibaca tablet untuk memilih papan; kosong berarti peran tanpa stasiun.
    station_id: str | None
    is_active: bool
    photo_url: str | None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUserOut


class BrowserSessionOut(BaseModel):
    """A browser sign-in: the token went into a cookie the page cannot read, so only its lifetime and the account come back."""

    expires_in: int
    user: AuthUserOut
