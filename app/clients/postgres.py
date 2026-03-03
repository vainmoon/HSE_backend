import asyncpg
import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_pg_connection() -> AsyncGenerator[None, asyncpg.Connection]:
    connection: asyncpg.Connection = await asyncpg.connect(
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'admin1'),
        database=os.getenv('POSTGRES_DB', 'avito_moderation'),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
    )

    yield connection

    await connection.close()