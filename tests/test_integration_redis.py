import pytest

from repositories.moderation_results import ModerationResultsRedisStorage

MODERATION_RESULT_DATA = {
    "id": 0,
    "item_id": 42,
    "status": "completed",
    "is_violation": True,
    "probability": 0.9,
    "error_message": None,
    "created_at": "2026-01-01 12:00:00",
    "processed_at": "2026-01-01 12:01:00",
}


def make_row(task_id: int) -> dict:
    return {**MODERATION_RESULT_DATA, "id": task_id}


@pytest.mark.integration
class TestModerationResultsRedisStorageIntegration:
    @pytest.mark.asyncio
    async def test_set_and_get_returns_stored_data(self):
        task_id = 99001
        storage = ModerationResultsRedisStorage()
        try:
            await storage.set(task_id, make_row(task_id))
            result = await storage.get(task_id)

            assert result is not None
            assert result["id"] == task_id
            assert result["status"] == "completed"
            assert result["is_violation"] is True
            assert result["probability"] == pytest.approx(0.9)
        finally:
            await storage.delete(task_id)

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(self):
        task_id = 99002
        storage = ModerationResultsRedisStorage()
        await storage.delete(task_id)

        result = await storage.get(task_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_key(self):
        task_id = 99003
        storage = ModerationResultsRedisStorage()
        await storage.set(task_id, make_row(task_id))

        await storage.delete(task_id)
        result = await storage.get(task_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_set_overwrites_existing_value(self):
        task_id = 99004
        storage = ModerationResultsRedisStorage()
        try:
            await storage.set(task_id, make_row(task_id))
            updated = {**make_row(task_id), "status": "failed"}
            await storage.set(task_id, updated)

            result = await storage.get(task_id)
            assert result["status"] == "failed"
        finally:
            await storage.delete(task_id)

    @pytest.mark.asyncio
    async def test_ttl_is_set_after_set(self):
        import redis.asyncio as aioredis

        task_id = 99005
        storage = ModerationResultsRedisStorage()
        try:
            await storage.set(task_id, make_row(task_id))

            conn = aioredis.Redis(host="redis", port=6379, decode_responses=True)
            ttl = await conn.ttl(str(task_id))
            await conn.aclose()

            assert ttl > 0
        finally:
            await storage.delete(task_id)
