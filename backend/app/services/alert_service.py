from app.models.alert import Alert, AlertCondition, AlertStatus
from app.models.alert_history import AlertHistory
from app.services.yfinance_service import yf_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime


class AlertService:
    async def evaluate_alert(self, alert: Alert, quote) -> bool:
        price = quote.price
        threshold = alert.threshold

        if alert.condition == AlertCondition.PRICE_ABOVE:
            return price > threshold
        elif alert.condition == AlertCondition.PRICE_BELOW:
            return price < threshold
        elif alert.condition == AlertCondition.PRICE_CROSSES:
            return abs(price - threshold) < (threshold * 0.001)
        elif alert.condition == AlertCondition.PCT_CHANGE_ABOVE:
            return quote.change_pct > threshold
        elif alert.condition == AlertCondition.PCT_CHANGE_BELOW:
            return quote.change_pct < threshold
        elif alert.condition == AlertCondition.VOLUME_ABOVE:
            return quote.volume > threshold
        return False

    async def check_all_alerts(self, db: AsyncSession):
        result = await db.execute(
            select(Alert).where(Alert.status == AlertStatus.ACTIVE)
        )
        alerts = result.scalars().all()

        triggered = []
        for alert in alerts:
            quote = await yf_service.get_quote(alert.ticker)
            if not quote:
                continue
            is_triggered = await self.evaluate_alert(alert, quote)
            if is_triggered:
                alert.status = AlertStatus.TRIGGERED
                alert.last_triggered_at = datetime.utcnow()
                history = AlertHistory(
                    alert_id=alert.id,
                    delivered_inapp=alert.channel_inapp,
                    delivered_email=alert.channel_email,
                    delivered_push=alert.channel_push,
                )
                db.add(history)
                triggered.append(alert)

        if triggered:
            await db.commit()
        return triggered


alert_service = AlertService()
