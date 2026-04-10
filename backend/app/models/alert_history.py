from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean
from datetime import datetime
from app.database import Base


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    delivered_inapp = Column(Boolean, default=False)
    delivered_email = Column(Boolean, default=False)
    delivered_push = Column(Boolean, default=False)
