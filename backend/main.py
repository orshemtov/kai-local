from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import BackgroundTasks, Depends, FastAPI, Response, status

from backend.clients.telegram.models import Update
from backend.clients.telegram.telegram import TelegramClient
from backend.db.pool import create_pool
from backend.deps import (
    get_telegram_client,
    get_webhook_service,
)
from backend.services.webhook_service import WebhookService
from backend.settings import settings
from backend.tasks.daily_report import daily_report
from backend.tasks.weekly_report import weekly_report


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database pool
    app.state.pool = await create_pool(settings.database_url)

    # Initialize and start scheduler
    scheduler = BackgroundScheduler()

    # Daily report job
    daily_trigger = CronTrigger(
        hour=20,
        minute=0,
    )  # Daily at 8:00 PM
    scheduler.add_job(
        daily_report,
        daily_trigger,
        [settings.chat_id],
        id="daily_report",
    )

    # Weekly report job
    weekly_trigger = CronTrigger(
        day_of_week="fri",
        hour=16,
        minute=0,
    )  # Weekly on Friday at 4:00 PM
    scheduler.add_job(
        weekly_report,
        weekly_trigger,
        [settings.chat_id],
        id="weekly_report",
    )

    scheduler.start()

    try:
        yield
    finally:
        await app.state.pool.close()
        scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/telegram/webhook")
async def telegram_webhook(
    payload: Update,
    background_tasks: BackgroundTasks,
    telegram: TelegramClient = Depends(get_telegram_client),
    webhook_service: WebhookService = Depends(get_webhook_service),
):
    background_tasks.add_task(webhook_service.process_update, payload, telegram)
    return Response(status_code=status.HTTP_200_OK)
