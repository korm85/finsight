from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.alert import AlertCondition, AlertStatus


class AlertCreate(BaseModel):
    ticker: str
    condition: AlertCondition
    threshold: float
    channel_inapp: bool = True
    channel_email: bool = False
    channel_push: bool = False


class AlertUpdate(BaseModel):
    condition: Optional[AlertCondition] = None
    threshold: Optional[float] = None
    channel_inapp: Optional[bool] = None
    channel_email: Optional[bool] = None
    channel_push: Optional[bool] = None
    status: Optional[AlertStatus] = None


class AlertResponse(BaseModel):
    id: int
    ticker: str
    condition: AlertCondition
    threshold: float
    channel_inapp: bool
    channel_email: bool
    channel_push: bool
    status: AlertStatus
    last_triggered_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    id: int
    alert_id: int
    ticker: str
    condition: AlertCondition
    threshold: float
    triggered_at: datetime
    delivered_inapp: bool
    delivered_email: bool
    delivered_push: bool
