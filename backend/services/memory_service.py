import datetime
import json

import asyncpg
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python


class MemoryService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def save(self, messages: list[ModelMessage]) -> None:
        """Save messages using pydantic-ai's built-in serialization."""
        try:
            serialized_messages = to_jsonable_python(messages)
            conn: asyncpg.Connection
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO memory (date, messages, updated_at)
                    VALUES ($1, $2, NOW())
                ON CONFLICT (date) DO UPDATE
                SET messages = EXCLUDED.messages,
                    updated_at = NOW()
                """,
                    datetime.date.today(),
                    json.dumps(serialized_messages),
                )
        except UnicodeDecodeError:
            # Skip saving when there's binary content
            return

    async def get(self) -> list[ModelMessage] | None:
        """Load messages using pydantic-ai's built-in deserialization."""
        today = datetime.date.today()
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT messages
                FROM memory
                WHERE date = $1
            """,
                today,
            )
        if not row:
            return None

        messages = (
            json.loads(row["messages"])
            if isinstance(row["messages"], str)
            else row["messages"]
        )

        return ModelMessagesTypeAdapter.validate_python(messages)
