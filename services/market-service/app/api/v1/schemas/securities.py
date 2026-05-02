from pydantic import BaseModel
from typing import Optional


class SecurityResponse(BaseModel):
    ticker:    str
    name:      str
    exchange:  Optional[str]
    sector:    Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class SecuritiesListResponse(BaseModel):
    items: list[SecurityResponse]
    total: int