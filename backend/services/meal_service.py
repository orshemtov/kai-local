import datetime
import uuid

import asyncpg

from backend.models import Ingredient, Meal


class MealService:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def save(self, meal: Meal) -> Meal:
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
            INSERT INTO meals (
                id,
                created_at,
                name,
                description,
                ingredients,
                calories,
                protein,
                carbs,
                fat
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
            """,
                meal.id,
                meal.created_at,
                meal.name,
                meal.description,
                [ingredient.model_dump() for ingredient in meal.ingredients],
                meal.calories,
                meal.protein,
                meal.carbs,
                meal.fat,
            )
        return meal

    async def update(self, id: uuid.UUID, meal: Meal) -> Meal:
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE meals
                SET name = $1,
                    description = $2,
                    ingredients = $3,
                calories = $4,
                protein = $5,
                carbs = $6,
                fat = $7
            WHERE id = $8;
            """,
                meal.name,
                meal.description,
                [ingredient.model_dump() for ingredient in meal.ingredients],
                meal.calories,
                meal.protein,
                meal.carbs,
                meal.fat,
                id,
            )

        # No rows updated means the meal was not found
        if result == "UPDATE 0":
            raise ValueError("Meal not found")

        return meal

    async def delete(self, id: uuid.UUID) -> None:
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM meals
                WHERE id = $1;
                """,
                id,
            )

        # No rows deleted means the meal was not found
        if result == "DELETE 0":
            raise ValueError("Meal not found")

    async def list_meals(
        self,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
    ) -> list[Meal]:
        conn: asyncpg.Connection
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    id,
                    created_at,
                name,
                description,
                ingredients,
                calories,
                protein,
                carbs,
                fat
            FROM meals
            WHERE created_at BETWEEN $1 AND $2
            ORDER BY created_at DESC;
            """,
                start_time,
                end_time,
            )
        meals = []
        for row in rows:
            row_dict = dict(row)
            row_dict["ingredients"] = [
                Ingredient(
                    **ingredient,
                )
                for ingredient in row_dict["ingredients"]
            ]
            meal = Meal(**row_dict)
            meals.append(meal)
        return meals
