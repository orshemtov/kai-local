import asyncio
from typing import Any, Callable

import asyncpg
from pydantic_ai import BinaryContent
from pydantic_ai.agent import AgentRunResult
from pydantic_ai.messages import ModelMessage

from backend.agent import Deps, agent
from backend.clients.telegram.models import (
    DocumentMessage,
    ImageMessage,
    TextMessage,
    Update,
    VoiceMessage,
)
from backend.clients.telegram.telegram import TelegramClient
from backend.services.meal_service import MealService
from backend.services.memory_service import MemoryService
from backend.services.transcriber import Transcriber
from backend.services.workout_service import WorkoutService


def notify_user_on_delay(seconds: int) -> Any:
    """Decorator to notify user after a delay, in case the processing takes time."""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create an event to signal when the main function completes
            completed = asyncio.Event()

            async def delayed_notification() -> None:
                """Send notification if processing takes too long."""
                try:
                    await asyncio.wait_for(completed.wait(), timeout=seconds)
                except asyncio.TimeoutError:
                    # Main function is still running after the delay
                    if len(args) >= 3:
                        payload = args[1]
                        telegram = args[2]
                        if isinstance(payload, Update) and isinstance(
                            telegram, TelegramClient
                        ):
                            telegram.send_message(
                                chat_id=payload.message.chat.id,
                                message="Processing your request, please wait a moment...",
                            )

            # Start the notification task
            notification_task = asyncio.create_task(delayed_notification())

            try:
                # Run the main function
                return await func(*args, **kwargs)
            finally:
                # Signal completion and cleanup
                completed.set()
                notification_task.cancel()
                try:
                    await notification_task
                except asyncio.CancelledError:
                    pass

        return wrapper

    return decorator


class WebhookService:
    """Service for handling Telegram webhook updates."""

    def __init__(self, pool: asyncpg.Pool, transcriber: Transcriber):
        self.pool = pool
        self.transcriber = transcriber

    async def process_text_message(
        self,
        payload: TextMessage,
        meal_service: MealService,
        workout_service: WorkoutService,
        telegram: TelegramClient,
        message_history: list[ModelMessage],
    ) -> AgentRunResult[str]:
        """Process a text message and return the result."""
        result = await agent.run(
            payload.text,
            deps=Deps(
                meal_service=meal_service,
                workout_service=workout_service,
            ),
            message_history=message_history,
        )

        telegram.send_message(
            chat_id=payload.chat.id,
            message=result.output,
        )

        return result

    async def process_image_message(
        self,
        payload: ImageMessage,
        caption: str | None,
        meal_service: MealService,
        workout_service: WorkoutService,
        telegram: TelegramClient,
        message_history: list[ModelMessage],
    ) -> AgentRunResult[str]:
        """Process an image message and return the result."""
        image = telegram.get_file(payload.images[0].file_id)

        result = await agent.run(
            [
                (
                    "The user have sent an image, verify if it's related to a meal or workout and process it accordingly. "
                    "If it's a meal, echo to the user the meal's name, calories, nutrients, ingredients you see, etc, estimate the quantity. "
                    "Log the meal in the database. "
                    "If it's a workout, echo to the user the workout's name, duration, calories burned, etc. "
                    "Log the workout in the database."
                ),
                (
                    f"User provided this caption to the image:\n{caption}"
                    if caption
                    else "No caption provided."
                ),
                BinaryContent(data=image, media_type="image/png"),
            ],
            deps=Deps(
                meal_service=meal_service,
                workout_service=workout_service,
            ),
            message_history=message_history,
        )

        telegram.send_message(
            chat_id=payload.chat.id,
            message=result.output,
        )

        return result

    async def process_voice_message(
        self,
        payload: VoiceMessage,
        meal_service: MealService,
        workout_service: WorkoutService,
        telegram: TelegramClient,
        message_history: list[ModelMessage],
    ) -> AgentRunResult[str] | None:
        """Process a voice message and return the result."""
        voice_message = telegram.get_file(payload.voice.file_id)

        # TODO: Use BinaryContent instead of transcribing the audio
        # Does not work out of the box because of the format, need to convert the audio to different format
        text = self.transcriber.transcribe(voice_message, payload.voice.mime_type)

        return await self.process_text_message(
            TextMessage(
                message_id=payload.message_id,
                chat=payload.chat,
                user=payload.user,  # type: ignore
                date=payload.date,
                text=text,
            ),
            meal_service,
            workout_service,
            telegram,
            message_history,
        )

    async def process_document_message(
        self,
        payload: DocumentMessage,
        meal_service: MealService,
        workout_service: WorkoutService,
        telegram: TelegramClient,
        message_history: list[ModelMessage],
    ) -> AgentRunResult[str]:
        """Process a document message and return the result."""
        document = telegram.get_file(payload.document.file_id)

        result = await agent.run(
            [
                "The user have sent a document, scan through it, verify if it's related to a meal or workout and process it accordingly.",
                BinaryContent(
                    data=document,
                    media_type=payload.document.mime_type,
                ),
            ],
            deps=Deps(
                meal_service=meal_service,
                workout_service=workout_service,
            ),
            message_history=message_history,
        )

        telegram.send_message(
            chat_id=payload.chat.id,
            message=result.output,
        )

        return result

    @notify_user_on_delay(seconds=3)
    async def process_update(
        self,
        payload: Update,
        telegram: TelegramClient,
    ) -> None:
        """Process a Telegram update with proper database connection management."""
        # Get fresh connections from pool for the background task
        meal_service = MealService(self.pool)
        workout_service = WorkoutService(self.pool)
        memory_service = MemoryService(self.pool)

        # Get message history once for all processors
        message_history = await memory_service.get()
        if not message_history:
            message_history = []

        result = None
        match payload.message:
            case TextMessage():
                result = await self.process_text_message(
                    payload.message,
                    meal_service,
                    workout_service,
                    telegram,
                    message_history,
                )
            case ImageMessage():
                result = await self.process_image_message(
                    payload.message,
                    payload.caption,
                    meal_service,
                    workout_service,
                    telegram,
                    message_history,
                )
            case VoiceMessage():
                result = await self.process_voice_message(
                    payload.message,
                    meal_service,
                    workout_service,
                    telegram,
                    message_history,
                )
            case DocumentMessage():
                result = await self.process_document_message(
                    payload.message,
                    meal_service,
                    workout_service,
                    telegram,
                    message_history,
                )

        # Save the updated message history if a result was produced
        if result:
            await memory_service.save(result.all_messages())
