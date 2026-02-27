import asyncpg
import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_pg_connection() -> AsyncGenerator[None, asyncpg.Connection]:
    connection: asyncpg.Connection = await asyncpg.connect(
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'admin1'),
        database=os.getenv('DB_NAME', 'avito_moderation'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432'))
    )

    yield connection

    await connection.close()