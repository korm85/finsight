from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional


class HoldingBase(BaseModel):
    ticker: str
    name: str
    quantity: float
    avg_cost: float
    purchase_date: Optional[date] = None


class HoldingCreate(HoldingBase):
    pass


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = None
    avg_cost: Optional[float] = None


class HoldingResponse(HoldingBase):
    id: int
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    holdings: List[HoldingResponse]
    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_pct: float
    day_pnl: float
