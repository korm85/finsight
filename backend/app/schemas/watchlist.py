from pydantic import BaseModel
from datetime import datetime
from typing import List


class WatchlistItemResponse(BaseModel):
    ticker: str
    name: str
    price: float
    change_pct: float


class WatchlistResponse(BaseModel):
    id: int
    name: str
    items: List[WatchlistItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    name: str


class WatchlistItemCreate(BaseModel):
    ticker: str
    name: str
