CREATE TABLE IF NOT EXISTS public.moderation_results (
    id            SERIAL PRIMARY KEY,
    item_id       INTEGER REFERENCES item(id) ON DELETE CASCADE,
    status        VARCHAR(20),
    is_violation  BOOLEAN,
    probability   FLOAT,
    error_message TEXT,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at  TIMESTAMP
);
