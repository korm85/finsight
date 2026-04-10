from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from app.database import get_db
from app.models.alert import Alert, AlertStatus
from app.models.alert_history import AlertHistory
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse, AlertHistoryResponse
from app.services.alert_service import alert_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertResponse])
async def get_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).order_by(desc(Alert.created_at)))
    return result.scalars().all()


@router.post("", response_model=AlertResponse)
async def create_alert(data: AlertCreate, db: AsyncSession = Depends(get_db)):
    alert = Alert(
        ticker=data.ticker.upper(),
        condition=data.condition,
        threshold=data.threshold,
        channel_inapp=data.channel_inapp,
        channel_email=data.channel_email,
        channel_push=data.channel_push,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int, data: AlertUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if data.condition is not None:
        alert.condition = data.condition
    if data.threshold is not None:
        alert.threshold = data.threshold
    if data.channel_inapp is not None:
        alert.channel_inapp = data.channel_inapp
    if data.channel_email is not None:
        alert.channel_email = data.channel_email
    if data.channel_push is not None:
        alert.channel_push = data.channel_push
    if data.status is not None:
        alert.status = data.status
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
    return {"success": True}


@router.get("/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AlertHistory, Alert)
        .join(Alert)
        .order_by(desc(AlertHistory.triggered_at))
        .limit(50)
    )
    rows = result.all()
    return [
        AlertHistoryResponse(
            id=h.id,
            alert_id=h.alert_id,
            ticker=a.ticker,
            condition=a.condition,
            threshold=a.threshold,
            triggered_at=h.triggered_at,
            delivered_inapp=h.delivered_inapp,
            delivered_email=h.delivered_email,
            delivered_push=h.delivered_push,
        )
        for h, a in rows
    ]
