CREATE TABLE IF NOT EXISTS public.moderation_results (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES public.item(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_violation BOOLEAN,
    probability FLOAT,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);