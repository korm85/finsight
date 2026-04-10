from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from datetime import datetime
from app.database import Base


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    purchase_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def market_value(self, current_price: float) -> float:
        return self.quantity * current_price

    def pnl(self, current_price: float) -> float:
        return (current_price - self.avg_cost) * self.quantity

    def pnl_pct(self, current_price: float) -> float:
        if self.avg_cost == 0:
            return 0.0
        return ((current_price - self.avg_cost) / self.avg_cost) * 100
