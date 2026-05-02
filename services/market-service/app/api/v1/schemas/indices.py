from pydantic import BaseModel
from typing import Optional


class MarketIndexResponse(BaseModel):
    index_code:  str
    name:        str
    description: Optional[str]
    is_active:   bool

    model_config = {"from_attributes": True}