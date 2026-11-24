"""Response parts shared by several sales reports."""
from pydantic import BaseModel, ConfigDict


class ResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomersOut(ResponseModel):
    visits: int
    unique: int
    new: int
    returning: int
