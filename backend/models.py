import datetime
import uuid
from typing import Literal

from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: str
    quantity: float


class Meal(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    name: str
    description: str | None = None
    ingredients: list[Ingredient]
    calories: int | None = None
    protein: int | None = None
    carbs: int | None = None
    fat: int | None = None


class Workout(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )
    name: Literal["swimming", "running", "walking", "weight-lifting"]
    type: Literal["cardio", "strength", "flexibility"]
    duration: int | None = None
    calories_burned: int | None = None
