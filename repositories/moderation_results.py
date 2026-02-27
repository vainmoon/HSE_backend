from datetime import datetime, timezone
from typing import Mapping, Any

from clients.postgres import get_pg_connection
from errors import ModerationResultNotFoundError
from models.moderation_results import ModerationResultModel


class ModerationResultPostgresStorage:
    async def create_pending(self, item_id: int) -> Mapping[str, Any]:
        query = '''
            INSERT INTO moderation_results (item_id, status)
            VALUES ($1::INTEGER, 'pending')
            RETURNING *
        '''
        async with get_pg_connection() as connection:
            return dict(await connection.fetchrow(query, item_id))

    async def select(self, task_id: int) -> Mapping[str, Any]:
        query = '''
            SELECT *
            FROM moderation_results
            WHERE id = $1::INTEGER
            LIMIT 1
        '''
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, task_id)

            if row:
                return dict(row)

            raise ModerationResultNotFoundError()

    async def update_completed(self, task_id: int, is_violation: bool, probability: float) -> Mapping[str, Any]:
        query = '''
            UPDATE moderation_results
            SET status = 'completed',
                is_violation = $2::BOOLEAN,
                probability = $3::FLOAT,
                processed_at = $4::TIMESTAMP
            WHERE id = $1::INTEGER
            RETURNING *
        '''
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(
                query, task_id, is_violation, probability, datetime.now(timezone.utc)
            )
            if row:
                return dict(row)
            raise ModerationResultNotFoundError()

    async def update_failed(self, task_id: int, error_message: str) -> Mapping[str, Any]:
        query = '''
            UPDATE moderation_results
            SET status = 'failed',
                error_message = $2::TEXT,
                processed_at = $3::TIMESTAMP
            WHERE id = $1::INTEGER
            RETURNING *
        '''
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(
                query, task_id, error_message, datetime.now(timezone.utc)
            )
            if row:
                return dict(row)
            raise ModerationResultNotFoundError()


class ModerationResultRepository:
    _storage = ModerationResultPostgresStorage()

    async def create_pending(self, item_id: int) -> ModerationResultModel:
        raw = await self._storage.create_pending(item_id)
        return ModerationResultModel(**raw)

    async def get_by_id(self, task_id: int) -> ModerationResultModel:
        raw = await self._storage.select(task_id)
        return ModerationResultModel(**raw)

    async def update_completed(self, task_id: int, is_violation: bool, probability: float) -> ModerationResultModel:
        raw = await self._storage.update_completed(task_id, is_violation, probability)
        return ModerationResultModel(**raw)

    async def update_failed(self, task_id: int, error_message: str) -> ModerationResultModel:
        raw = await self._storage.update_failed(task_id, error_message)
        return ModerationResultModel(**raw)
