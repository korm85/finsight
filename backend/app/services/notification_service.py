import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings
from typing import Optional
import json

settings = get_settings()


class NotificationService:
    async def send_email(
        self, to_email: str, subject: str, body: str
    ) -> bool:
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return False
        message = MIMEMultipart("alternative")
        message["From"] = settings.SMTP_USER
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            return True
        except Exception:
            return False

    async def send_browser_push(
        self, subscription_json: str, title: str, body: str
    ) -> bool:
        try:
            from webpush import WebPush
            subscription = json.loads(subscription_json)
            vapid_email = settings.VAPID_EMAIL
            WebPush(
                subscription,
                json.dumps({"title": title, "body": body}),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_c=vapid_email,
            ).send()
            return True
        except Exception:
            return False

    def format_alert_message(self, ticker: str, condition: str, threshold: float) -> str:
        condition_text = {
            "price_above": f"crossed above ${threshold:.2f}",
            "price_below": f"crossed below ${threshold:.2f}",
            "pct_change_above": f"gained {threshold}%",
            "pct_change_below": f"dropped {threshold}%",
            "volume_above": f"had volume above {int(threshold):,}",
        }.get(condition, f"triggered condition {condition}")
        return f"{ticker} {condition_text}"


notification_service = NotificationService()
