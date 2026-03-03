from clients.postgres import get_pg_connection
from models.moderation_results import ModerationResultModel


class ModerationResultsPostgresStorage:
    async def create(self, item_id: int) -> int:
        query = '''
            INSERT INTO moderation_results (item_id, status)
            VALUES ($1, 'pending')
            RETURNING *
        '''
        async with get_pg_connection() as connection:
            return await connection.fetchrow(query, item_id)
        
        
class ModerationResultsRepository:
    moderation_results_postgres_storage = ModerationResultsPostgresStorage()

    async def create(self, item_id: int) -> ModerationResultModel:
        result = await self.moderation_results_postgres_storage.create(item_id)
        return ModerationResultModel(**result)