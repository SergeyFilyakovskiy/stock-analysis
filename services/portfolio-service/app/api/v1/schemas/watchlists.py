from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WatchlistCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WatchlistItemAddRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20)


class WatchlistItemResponse(BaseModel):
    id: UUID
    ticker: str
    added_at: datetime

    model_config = {"from_attributes": True}


class WatchlistResponse(BaseModel):
    id: UUID
    name: str
    user_id: UUID
    created_at: datetime
    items: list[WatchlistItemResponse] = []

    model_config = {"from_attributes": True}


class WatchlistListResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}