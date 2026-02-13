CREATE TABLE IF NOT EXISTS public.seller (
    id SERIAL PRIMARY KEY,
    is_verified_seller BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS public.item (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    images_qty INT NOT NULL,
    seller_id INT NOT NULL,

    FOREIGN KEY (seller_id)
        REFERENCES seller(id)
        ON DELETE CASCADE
);