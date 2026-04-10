from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery("finsight", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "check-alerts-every-5-minutes": {
        "task": "app.tasks.alert_tasks.check_alerts_task",
        "schedule": 300.0,
    },
}
