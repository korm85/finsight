from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String, default="Investor")
    email = Column(String, nullable=True)
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=False)
    push_subscription = Column(String, nullable=True)
    refresh_rate = Column(Integer, default=60)
