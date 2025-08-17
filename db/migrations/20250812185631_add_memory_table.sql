-- migrate:up
CREATE TABLE memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    messages JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(date)
);
-- Create an index on the date column for efficient queries
CREATE INDEX idx_memory_date ON memory(date);
-- migrate:down
DROP TABLE memory;