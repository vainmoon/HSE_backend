import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

from repositories.items import ItemPostgresStorage
from repositories.sellers import SellerPostgresStorage
from errors import SellerNotFoundError, ItemNotFoundError

@pytest.fixture
def pg_mock(monkeypatch):
    mock_connection = AsyncMock()

    @asynccontextmanager
    async def fake_get_pg_connection():
        yield mock_connection

    monkeypatch.setattr("repositories.items.get_pg_connection", fake_get_pg_connection)
    monkeypatch.setattr("repositories.sellers.get_pg_connection", fake_get_pg_connection)

    return mock_connection


@pytest.fixture
def seller_storage():
    return SellerPostgresStorage()


@pytest.fixture
def item_storage():
    return ItemPostgresStorage()


class TestSellerRepository:
    @pytest.mark.asyncio
    async def test_create_seller_success(self, pg_mock, seller_storage):
        seller_data = {"id": 1, "is_verified_seller": True}
        pg_mock.fetchrow.return_value = seller_data

        result = await seller_storage.create(is_verified_seller=True)

        assert result == seller_data

    @pytest.mark.asyncio
    async def test_get_seller_not_found(self, pg_mock, seller_storage):
        pg_mock.fetchrow.return_value = None

        with pytest.raises(SellerNotFoundError):
            await seller_storage.select(id=-1)

    @pytest.mark.asyncio
    async def test_delete_seller_success(self, pg_mock, seller_storage):
        seller_data = {"id": 2, "is_verified_seller": False}
        pg_mock.fetchrow.return_value = seller_data

        deleted = await seller_storage.delete(id=2)

        assert deleted["id"] == 2


class TestItemRepository:
    @pytest.mark.asyncio
    async def test_create_item_success(self, pg_mock, item_storage):
        item_data = {
            "id": 1,
            "name": "Test Item",
            "description": "Test",
            "category": 1,
            "images_qty": 2,
            "seller_id": 1,
        }
        pg_mock.fetchrow.return_value = item_data

        result = await item_storage.create(
            name=item_data["name"],
            description=item_data["description"],
            category=item_data["category"],
            images_qty=item_data["images_qty"],
            seller_id=item_data["seller_id"],
        )

        assert result == item_data
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_get_item_not_found(self, pg_mock, item_storage):
        pg_mock.fetchrow.return_value = None

        with pytest.raises(ItemNotFoundError):
            await item_storage.select(id=-1)


    @pytest.mark.asyncio
    async def test_delete_item_success(self, pg_mock, item_storage):
        item_data = {
            "id": 5,
            "name": "ToDelete",
            "description": "x",
            "category": 1,
            "images_qty": 1,
            "seller_id": 1,
        }
        pg_mock.fetchrow.return_value = item_data

        deleted = await item_storage.delete(id=5)

        assert deleted["id"] == 5