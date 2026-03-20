import pytest

from repositories.sellers import SellerPostgresStorage
from repositories.items import ItemPostgresStorage
from repositories.moderation_results import ModerationResultsPostgresStorage
from repositories.accounts import AccountPostgresStorage
from errors import SellerNotFoundError, ItemNotFoundError, ModerationResultNotFoundError, AccountNotFoundError


@pytest.mark.integration
class TestSellerPostgresStorageIntegration:
    @pytest.mark.asyncio
    async def test_create_returns_seller_with_id(self):
        storage = SellerPostgresStorage()
        seller = await storage.create(is_verified_seller=False)
        try:
            assert seller["id"] > 0
            assert seller["is_verified_seller"] is False
        finally:
            await storage.delete(id=seller["id"])

    @pytest.mark.asyncio
    async def test_select_returns_created_seller(self):
        storage = SellerPostgresStorage()
        seller = await storage.create(is_verified_seller=True)
        try:
            result = await storage.select(id=seller["id"])
            assert result["id"] == seller["id"]
            assert result["is_verified_seller"] is True
        finally:
            await storage.delete(id=seller["id"])

    @pytest.mark.asyncio
    async def test_select_not_found_raises(self):
        storage = SellerPostgresStorage()
        with pytest.raises(SellerNotFoundError):
            await storage.select(id=999999)

    @pytest.mark.asyncio
    async def test_delete_removes_seller(self):
        storage = SellerPostgresStorage()
        seller = await storage.create(is_verified_seller=True)
        await storage.delete(id=seller["id"])
        with pytest.raises(SellerNotFoundError):
            await storage.select(id=seller["id"])


@pytest.mark.integration
class TestItemPostgresStorageIntegration:
    @pytest.mark.asyncio
    async def test_create_returns_item_with_id(self):
        sellers = SellerPostgresStorage()
        items = ItemPostgresStorage()
        seller = await sellers.create(is_verified_seller=True)
        try:
            item = await items.create(
                name="New Item", description="desc", category=1, images_qty=0, seller_id=seller["id"]
            )
            try:
                assert item["id"] > 0
                assert item["name"] == "New Item"
                assert item["seller_id"] == seller["id"]
            finally:
                await items.delete(id=item["id"])
        finally:
            await sellers.delete(id=seller["id"])

    @pytest.mark.asyncio
    async def test_select_returns_item(self):
        sellers = SellerPostgresStorage()
        items = ItemPostgresStorage()
        seller = await sellers.create(is_verified_seller=True)
        try:
            item = await items.create(
                name="Select Test", description="desc", category=1, images_qty=1, seller_id=seller["id"]
            )
            try:
                result = await items.select(id=item["id"])
                assert result["id"] == item["id"]
                assert result["name"] == item["name"]
            finally:
                await items.delete(id=item["id"])
        finally:
            await sellers.delete(id=seller["id"])

    @pytest.mark.asyncio
    async def test_select_not_found_raises(self):
        storage = ItemPostgresStorage()
        with pytest.raises(ItemNotFoundError):
            await storage.select(id=999999)

    @pytest.mark.asyncio
    async def test_delete_removes_item(self):
        sellers = SellerPostgresStorage()
        items = ItemPostgresStorage()
        seller = await sellers.create(is_verified_seller=False)
        try:
            item = await items.create(
                name="Delete Test", description="desc", category=1, images_qty=0, seller_id=seller["id"]
            )
            await items.delete(id=item["id"])
            with pytest.raises(ItemNotFoundError):
                await items.select(id=item["id"])
        finally:
            await sellers.delete(id=seller["id"])

    @pytest.mark.asyncio
    async def test_select_with_seller_returns_joined_data(self):
        sellers = SellerPostgresStorage()
        items = ItemPostgresStorage()
        seller = await sellers.create(is_verified_seller=True)
        try:
            item = await items.create(
                name="Join Test", description="desc", category=2, images_qty=3, seller_id=seller["id"]
            )
            try:
                result = await items.select_with_seller(id=item["id"])
                assert result["item_id"] == item["id"]
                assert result["seller_id"] == seller["id"]
                assert "is_verified_seller" in result
            finally:
                await items.delete(id=item["id"])
        finally:
            await sellers.delete(id=seller["id"])


@pytest.mark.integration
class TestModerationResultsPostgresStorageIntegration:
    @pytest.mark.asyncio
    async def test_create_returns_pending_result(self):
        sellers = SellerPostgresStorage()
        items = ItemPostgresStorage()
        moderation = ModerationResultsPostgresStorage()
        seller = await sellers.create(is_verified_seller=True)
        try:
            item = await items.create(
                name="Mod Test", description="desc", category=1, images_qty=0, seller_id=seller["id"]
            )
            try:
                result = await moderation.create(item_id=item["id"])
                try:
                    assert result["id"] > 0
                    assert result["item_id"] == item["id"]
                    assert result["status"] == "pending"
                    assert result["is_violation"] is None
                finally:
                    await moderation.delete_by_item_id(item_id=item["id"])
            finally:
                await items.delete(id=item["id"])
        finally:
            await sellers.delete(id=seller["id"])

    @pytest.mark.asyncio
    async def test_select_returns_created_result(self):
        sellers = SellerPostgresStorage()
        items = ItemPostgresStorage()
        moderation = ModerationResultsPostgresStorage()
        seller = await sellers.create(is_verified_seller=True)
        try:
            item = await items.create(
                name="Select Mod", description="desc", category=1, images_qty=0, seller_id=seller["id"]
            )
            try:
                created = await moderation.create(item_id=item["id"])
                try:
                    result = await moderation.select(id=created["id"])
                    assert result["id"] == created["id"]
                    assert result["status"] == "pending"
                finally:
                    await moderation.delete_by_item_id(item_id=item["id"])
            finally:
                await items.delete(id=item["id"])
        finally:
            await sellers.delete(id=seller["id"])

    @pytest.mark.asyncio
    async def test_select_not_found_raises(self):
        storage = ModerationResultsPostgresStorage()
        with pytest.raises(ModerationResultNotFoundError):
            await storage.select(id=999999)

    @pytest.mark.asyncio
    async def test_update_changes_status_and_result(self):
        sellers = SellerPostgresStorage()
        items = ItemPostgresStorage()
        moderation = ModerationResultsPostgresStorage()
        seller = await sellers.create(is_verified_seller=True)
        try:
            item = await items.create(
                name="Update Mod", description="desc", category=1, images_qty=0, seller_id=seller["id"]
            )
            try:
                created = await moderation.create(item_id=item["id"])
                try:
                    updated = await moderation.update(
                        id=created["id"],
                        status="completed",
                        is_violation=True,
                        probability=0.95,
                    )
                    assert updated["status"] == "completed"
                    assert updated["is_violation"] is True
                    assert abs(updated["probability"] - 0.95) < 1e-6
                finally:
                    await moderation.delete_by_item_id(item_id=item["id"])
            finally:
                await items.delete(id=item["id"])
        finally:
            await sellers.delete(id=seller["id"])

    @pytest.mark.asyncio
    async def test_delete_by_item_id_removes_all_results(self):
        sellers = SellerPostgresStorage()
        items = ItemPostgresStorage()
        moderation = ModerationResultsPostgresStorage()
        seller = await sellers.create(is_verified_seller=True)
        try:
            item = await items.create(
                name="Delete Mod", description="desc", category=1, images_qty=0, seller_id=seller["id"]
            )
            try:
                created = await moderation.create(item_id=item["id"])
                deleted = await moderation.delete_by_item_id(item_id=item["id"])
                assert len(deleted) >= 1
                assert any(r["id"] == created["id"] for r in deleted)
                with pytest.raises(ModerationResultNotFoundError):
                    await moderation.select(id=created["id"])
            finally:
                await items.delete(id=item["id"])
        finally:
            await sellers.delete(id=seller["id"])

    @pytest.mark.asyncio
    async def test_delete_by_item_id_returns_empty_when_no_results(self):
        sellers = SellerPostgresStorage()
        items = ItemPostgresStorage()
        moderation = ModerationResultsPostgresStorage()
        seller = await sellers.create(is_verified_seller=True)
        try:
            item = await items.create(
                name="Empty Mod", description="desc", category=1, images_qty=0, seller_id=seller["id"]
            )
            try:
                deleted = await moderation.delete_by_item_id(item_id=item["id"])
                assert deleted == []
            finally:
                await items.delete(id=item["id"])
        finally:
            await sellers.delete(id=seller["id"])


@pytest.mark.integration
class TestAccountPostgresStorageIntegration:
    @pytest.mark.asyncio
    async def test_create_returns_account_with_id(self):
        storage = AccountPostgresStorage()
        account = await storage.create(login="user1", password="pass1")
        try:
            assert account["id"] > 0
            assert account["login"] == "user1"
            assert account["password"] == "pass1"
            assert account["is_blocked"] is False
        finally:
            await storage.delete(id=account["id"])

    @pytest.mark.asyncio
    async def test_select_returns_created_account(self):
        storage = AccountPostgresStorage()
        account = await storage.create(login="user2", password="pass2")
        try:
            result = await storage.select(id=account["id"])
            assert result["id"] == account["id"]
            assert result["login"] == "user2"
        finally:
            await storage.delete(id=account["id"])

    @pytest.mark.asyncio
    async def test_select_not_found_raises(self):
        storage = AccountPostgresStorage()
        with pytest.raises(AccountNotFoundError):
            await storage.select(id=999999)

    @pytest.mark.asyncio
    async def test_delete_removes_account(self):
        storage = AccountPostgresStorage()
        account = await storage.create(login="user3", password="pass3")
        await storage.delete(id=account["id"])
        with pytest.raises(AccountNotFoundError):
            await storage.select(id=account["id"])

    @pytest.mark.asyncio
    async def test_block_sets_is_blocked_true(self):
        storage = AccountPostgresStorage()
        account = await storage.create(login="user4", password="pass4")
        try:
            blocked = await storage.block(id=account["id"])
            assert blocked["is_blocked"] is True
        finally:
            await storage.delete(id=account["id"])

    @pytest.mark.asyncio
    async def test_select_by_login_and_password_returns_account(self):
        storage = AccountPostgresStorage()
        account = await storage.create(login="user5", password="pass5")
        try:
            result = await storage.select_by_login_and_password(login="user5", password="pass5")
            assert result["id"] == account["id"]
            assert result["login"] == "user5"
        finally:
            await storage.delete(id=account["id"])

    @pytest.mark.asyncio
    async def test_select_by_login_and_password_wrong_credentials_raises(self):
        storage = AccountPostgresStorage()
        with pytest.raises(AccountNotFoundError):
            await storage.select_by_login_and_password(login="nouser", password="nopass")
