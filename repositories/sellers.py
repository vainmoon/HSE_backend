from typing import Mapping, Any, Sequence

from clients.postgres import get_pg_connection
from errors import SellerNotFoundError
from models.sellers import SellerModel

class  SellerPostgresStorage:
    async def create(self, is_verified_seller: bool) -> Mapping[str, Any]:
        query = '''
            INSERT INTO seller (is_verified_seller)
            VALUES ($1::BOOLEAN)
            RETURNING *
        '''

        async with get_pg_connection() as connection:
            return dict(await connection.fetchrow(query, is_verified_seller))
    
    async def delete(self, id: int) -> Mapping[str, Any]:
        query = '''
            DELETE FROM seller
            WHERE id = $1::INTEGER
            RETURNING *
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id)

            if row:
                return dict(row)
            
            raise SellerNotFoundError()
    
    async def select(self, id: int) -> Mapping[str, Any]:
        query = '''
            SELECT *
            FROM seller
            WHERE id = $1::INTEGER
            LIMIT 1
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id)

            if row:
                return dict(row)
            
            raise SellerNotFoundError()

    async def select_many(self) -> Sequence[Mapping[str, Any]]:
        query = '''
            SELECT *
            FROM seller
        '''

        async with get_pg_connection() as connection:
            rows = await connection.fetch(query)

            return [dict(row) for row in rows]

    async def update(self, id: int, **updates: Any) -> Mapping[str, Any]:
        keys, args = [], []

        for key, value in updates.items():
            keys.append(key)
            args.append(value)

        fields_str = ', '.join([f'{key} = ${i + 2}' for i, key in enumerate(keys)])

        query = f'''
            UPDATE seller
            SET {fields_str}
            WHERE id = $1::INTEGER
            RETURNING *
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id, *args)

            if row:
                return dict(row)
            
            raise SellerNotFoundError()

class SellerRepository:
    seller_postgres_storage: SellerPostgresStorage = SellerPostgresStorage()

    async def create(self, is_verified_seller: bool) -> SellerModel:
        raw_seller = await self.seller_postgres_storage.create(is_verified_seller)
        return SellerModel(**raw_seller)

    async def get(self, seller_id: int) -> SellerModel:
        raw_seller = await self.seller_postgres_storage.select(seller_id)
        return SellerModel(**raw_seller)

    async def delete(self, seller_id: int) -> SellerModel:
        raw_seller = await self.seller_postgres_storage.delete(seller_id)
        return SellerModel(**raw_seller)

    async def update(self, seller_id: int, **changes: Mapping[str, Any]) -> SellerModel:
        raw_seller = await self.seller_postgres_storage.update(seller_id, **changes)
        return SellerModel(**raw_seller)
    
    async def get_many(self) -> Sequence[SellerModel]:
        return [
            SellerModel(**raw_seller)
            for raw_seller
            in await self.seller_postgres_storage.select_many()
        ]