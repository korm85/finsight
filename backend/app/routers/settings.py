from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.settings import SettingsResponse, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])

DEFAULT_USER_ID = 1


@router.get("", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == DEFAULT_USER_ID))
    user = result.scalar_one_or_none()
    if not user:
        user = User(id=DEFAULT_USER_ID, display_name="Investor")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return SettingsResponse(
        display_name=user.display_name,
        email=user.email,
        email_notifications=user.email_notifications,
        push_notifications=user.push_notifications,
        refresh_rate=user.refresh_rate,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == DEFAULT_USER_ID))
    user = result.scalar_one_or_none()
    if not user:
        user = User(id=DEFAULT_USER_ID)
        db.add(user)
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.email is not None:
        user.email = data.email
    if data.email_notifications is not None:
        user.email_notifications = data.email_notifications
    if data.push_notifications is not None:
        user.push_notifications = data.push_notifications
    if data.push_subscription is not None:
        user.push_subscription = data.push_subscription
    if data.refresh_rate is not None:
        user.refresh_rate = data.refresh_rate
    await db.commit()
    await db.refresh(user)
    return SettingsResponse(
        display_name=user.display_name,
        email=user.email,
        email_notifications=user.email_notifications,
        push_notifications=user.push_notifications,
        refresh_rate=user.refresh_rate,
    )