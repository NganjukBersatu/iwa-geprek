from pydantic import BaseModel


class PoolUserOut(BaseModel):
    id: str
    outlet_id: str | None
    username: str
    name: str | None
    role_name: str
