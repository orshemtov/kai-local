import asyncpg
from fastapi import Depends, Request

from backend.clients.telegram.telegram import TelegramClient
from backend.services.transcriber import Transcriber
from backend.services.webhook_service import WebhookService
from backend.settings import settings


async def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


def get_telegram_client() -> TelegramClient:
    return TelegramClient(bot_token=settings.bot_token)


async def get_webhook_service(pool: asyncpg.Pool = Depends(get_pool)) -> WebhookService:
    transcriber = Transcriber()
    return WebhookService(pool, transcriber)
