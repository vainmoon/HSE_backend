CREATE TABLE public.account
(
    id SERIAL,
    login TEXT NOT NULL,
    password TEXT NOT NULL,
    is_blocked BOOL NOT NULL DEFAULT FALSE
);
