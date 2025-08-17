-- migrate:up
CREATE TABLE meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name TEXT NOT NULL,
    description TEXT,
    ingredients JSONB NOT NULL,
    calories INTEGER,
    protein INTEGER,
    carbs INTEGER,
    fat INTEGER
);
CREATE TABLE workouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    name TEXT NOT NULL,
    type TEXT,
    duration INTEGER,
    calories_burned INTEGER
);
-- migrate:down
DROP TABLE meals;
DROP TABLE workouts;