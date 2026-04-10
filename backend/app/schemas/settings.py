from pydantic import BaseModel
from typing import Optional


class SettingsResponse(BaseModel):
    display_name: str
    email: Optional[str]
    email_notifications: bool
    push_notifications: bool
    refresh_rate: int


class SettingsUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[str] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    push_subscription: Optional[str] = None
    refresh_rate: Optional[int] = None
