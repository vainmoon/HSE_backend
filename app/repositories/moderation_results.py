from typing import Mapping, Any, Sequence

from clients.postgres import get_pg_connection
from models.moderation_results import ModerationResultModel
from errors import ModerationResultNotFoundError

class ModerationResultsPostgresStorage:
    async def create(self, item_id: int) -> Mapping[str, Any]:
        query = '''
            INSERT INTO moderation_results (item_id, status)
            VALUES ($1::INTEGER, 'pending')
            RETURNING *
        '''
        async with get_pg_connection() as connection:
            return dict(await connection.fetchrow(query, item_id))
        
    async def select(self, id: int) -> Mapping[str, Any]:
        query = '''
            SELECT * 
            FROM moderation_results
            WHERE id = $1::INTEGER
            LIMIT 1
        '''
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id)

            if row:
                return dict(row)

            raise ModerationResultNotFoundError()
        
        
class ModerationResultsRepository:
    moderation_results_postgres_storage = ModerationResultsPostgresStorage()

    async def create(self, item_id: int) -> ModerationResultModel:
        result = await self.moderation_results_postgres_storage.create(item_id)
        return ModerationResultModel(**result)
    
    async def select(self, id: int) -> ModerationResultModel:
        result = await self.moderation_results_postgres_storage.select(id)
        return ModerationResultModel(**result)