from typing import Mapping, Any, Sequence

from clients.postgres import get_pg_connection
from errors import ItemNotFoundError
from models.items import ItemModel, ItemWithSellerModel

class ItemPostgresStorage:
    async def create(self, name: str, description: str, category: int, images_qty: int, seller_id: int) -> Mapping[str, Any]:
        query = '''
            INSERT INTO item (name, description, category, images_qty, seller_id)
            VALUES ($1::TEXT, $2::TEXT, $3::INTEGER, $4::INTEGER, $5::INTEGER)
            RETURNING *
        '''

        async with get_pg_connection() as connection:
            return dict(await connection.fetchrow(query, name, description, category, images_qty, seller_id))
    
    async def delete(self, id: int) -> Mapping[str, Any]:
        query = '''
            DELETE FROM item
            WHERE id = $1::INTEGER
            RETURNING *
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id)

            if row:
                return dict(row)
            
            raise ItemNotFoundError()
    
    async def select(self, id: int) -> Mapping[str, Any]:
        query = '''
            SELECT *
            FROM item
            WHERE id = $1::INTEGER
            LIMIT 1
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id)

            if row:
                return dict(row)

            raise ItemNotFoundError()

    async def select_with_seller(self, id: int) -> Mapping[str, Any]:
        query = '''
            SELECT
                item.id AS item_id,
                item.name,
                item.description,
                item.category,
                item.images_qty,
                seller.id AS seller_id,
                seller.is_verified_seller
            FROM item
            JOIN seller ON item.seller_id = seller.id
            WHERE item.id = $1::INTEGER
            LIMIT 1
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id)

            if row:
                return dict(row)

            raise ItemNotFoundError()

    async def select_many(self) -> Sequence[Mapping[str, Any]]:
        query = '''
            SELECT *
            FROM item
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
            UPDATE item
            SET {fields_str}
            WHERE id = $1::INTEGER
            RETURNING *
        '''

        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id, *args)

            if row:
                return dict(row)
            
            raise ItemNotFoundError()

class ItemRepository:
    item_postgres_storage: ItemPostgresStorage = ItemPostgresStorage()

    async def create(self, name: str, description: str, category: int, images_qty: int, seller_id: int) -> ItemModel:
        raw_item = await self.item_postgres_storage.create(name, description, category, images_qty, seller_id)
        return ItemModel(**raw_item)

    async def get_with_seller(self, item_id: int) -> ItemWithSellerModel:
        raw = await self.item_postgres_storage.select_with_seller(item_id)
        return ItemWithSellerModel(**raw)

    async def get(self, item_id: int) -> ItemModel:
        raw_item = await self.item_postgres_storage.select(item_id)
        return ItemModel(**raw_item)

    async def delete(self, item_id: int) -> ItemModel:
        raw_item = await self.item_postgres_storage.delete(item_id)
        return ItemModel(**raw_item)

    async def update(self, item_id: int, **changes: Mapping[str, Any]) -> ItemModel:
        raw_item = await self.item_postgres_storage.update(item_id, **changes)
        return ItemModel(**raw_item)
    
    async def get_many(self) -> Sequence[ItemModel]:
        return [
            ItemModel(**raw_item)
            for raw_item
            in await self.item_postgres_storage.select_many()
        ]