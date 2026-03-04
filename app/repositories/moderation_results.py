from typing import Mapping, Any, Sequence
from datetime import timedelta
from json import dumps, loads


from clients.postgres import get_pg_connection
from clients.redis import get_redis_connection
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

    async def delete_by_item_id(self, item_id: int) -> Sequence[Mapping[str, Any]]:
        query = '''
            DELETE FROM moderation_results
            WHERE item_id = $1::INTEGER
            RETURNING *
        '''
        async with get_pg_connection() as connection:
            rows = await connection.fetch(query, item_id)
            return [dict(row) for row in rows]

    async def update(self, id: int, **updates: Any) -> Mapping[str, Any]:
        keys, args = [], []

        for key, value in updates.items():
            keys.append(key)
            args.append(value)

        fields_str = ', '.join([f'{key} = ${i + 2}' for i, key in enumerate(keys)])

        query = f'''
            UPDATE moderation_results
            SET {fields_str}
            WHERE id = $1::INTEGER
            RETURNING *
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id, *args)

            if row:
                return dict(row)
            
            raise ModerationResultNotFoundError()
        
class ModerationResultsRedisStorage:
    # TTL = 5 минут.
    # Так как в нашей системе пользователь может часто пинговать сервис, пока модель инференсит результат,
    # то есть смысл держать результат в кеше, чтобы не дергать базу данных при каждом запросе.
    # Если время инференса модели будет больше, то можно увеличить TTL, чтобы результат дольше держался в кеше.
    _TTL: timedelta = timedelta(minutes=5)

    async def delete(self, row_id: int) -> None:
        async with get_redis_connection() as connection:
            await connection.delete(str(row_id))

    async def set(self, row_id: int, row: Mapping[str, Any]) -> None:
        async with get_redis_connection() as connection:
            pipeline = connection.pipeline()
            pipeline.set(
                name=str(row_id),
                value=dumps(row, default=str)
            )
            pipeline.expire(str(row_id), self._TTL)
            await pipeline.execute()
    
    async def get(self, row_id: int) -> Mapping[str, Any] | None:
        async with get_redis_connection() as connection:
            row = await connection.get(str(row_id))

            if row:
                return loads(row)
            
            return None


class ModerationResultsRepository:
    moderation_results_postgres_storage = ModerationResultsPostgresStorage()
    moderation_results_redis_storage = ModerationResultsRedisStorage()

    async def create(self, item_id: int) -> ModerationResultModel:
        result = await self.moderation_results_postgres_storage.create(item_id)
        return ModerationResultModel(**result)
    
    async def select(self, id: int) -> ModerationResultModel:
        if result := await self.moderation_results_redis_storage.get(id):
            return ModerationResultModel(**result)
        
        result = await self.moderation_results_postgres_storage.select(id)
        await self.moderation_results_redis_storage.set(id, result)

        return ModerationResultModel(**result)

    async def delete_by_item_id(self, item_id: int) -> list[ModerationResultModel]:
        deleted = await self.moderation_results_postgres_storage.delete_by_item_id(item_id)
        for row in deleted:
            await self.moderation_results_redis_storage.delete(row["id"])
        return [ModerationResultModel(**row) for row in deleted]

    async def update(self, id: int, **changes) -> ModerationResultModel:
        result = await self.moderation_results_postgres_storage.update(id, **changes)
        await self.moderation_results_redis_storage.set(id, result)
        return ModerationResultModel(**result)