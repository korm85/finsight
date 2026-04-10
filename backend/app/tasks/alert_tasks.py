from celery import shared_task
from app.database import async_session_maker
from app.services.alert_service import alert_service


@shared_task
def check_alerts_task():
    import asyncio
    async def run():
        async with async_session_maker() as db:
            triggered = await alert_service.check_all_alerts(db)
            return len(triggered)
    return asyncio.run(run())
