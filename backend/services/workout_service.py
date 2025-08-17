import datetime
import uuid

import asyncpg

from backend.models import Workout


class WorkoutService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def save(self, workout: Workout) -> Workout:
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
            INSERT INTO workouts (
                id,
                created_at,
                name,
                type,
                duration,
                calories_burned
            ) VALUES ($1, $2, $3, $4, $5, $6);
            """,
                workout.id,
                workout.created_at,
                workout.name,
                workout.type,
                workout.duration,
                workout.calories_burned,
            )
        return workout

    async def update(self, id: uuid.UUID, workout: Workout) -> Workout:
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE workouts
                SET name = $1,
                    type = $2,
                    duration = $3,
                calories_burned = $4
            WHERE id = $5;
            """,
                workout.name,
                workout.type,
                workout.duration,
                workout.calories_burned,
                id,
            )

        # No rows updated means the workout was not found
        if result == "UPDATE 0":
            raise ValueError("Workout not found")

        return workout

    async def list_workouts(
        self,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
    ) -> list[Workout]:
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id,
                created_at,
                name,
                type,
                duration,
                calories_burned
            FROM workouts
            WHERE created_at BETWEEN $1 AND $2
            ORDER BY created_at DESC;
            """,
                start_time,
                end_time,
            )
        return [Workout(**row) for row in rows]
