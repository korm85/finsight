from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum as SAEnum
from datetime import datetime
from app.database import Base
import enum


class AlertCondition(str, enum.Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CROSSES = "price_crosses"
    PCT_CHANGE_ABOVE = "pct_change_above"
    PCT_CHANGE_BELOW = "pct_change_below"
    VOLUME_ABOVE = "volume_above"
    EARNINGS_WITHIN = "earnings_within"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    TRIGGERED = "triggered"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    condition = Column(SAEnum(AlertCondition), nullable=False)
    threshold = Column(Float, nullable=False)
    channel_inapp = Column(Boolean, default=True)
    channel_email = Column(Boolean, default=False)
    channel_push = Column(Boolean, default=False)
    status = Column(SAEnum(AlertStatus), default=AlertStatus.ACTIVE)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
