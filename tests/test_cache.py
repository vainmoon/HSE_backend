import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from repositories.moderation_results import (
    ModerationResultsRepository,
    ModerationResultsRedisStorage,
)
from models.moderation_results import ModerationResultModel


TASK_ID = 1

MODERATION_RESULT_DATA = {
    "id": TASK_ID,
    "item_id": 42,
    "status": "completed",
    "is_violation": True,
    "probability": 0.9,
    "error_message": None,
    "created_at": datetime(2026, 1, 1, 12, 0, 0),
    "processed_at": datetime(2026, 1, 1, 12, 1, 0),
}


class TestModerationResultsRepositoryCache:
    @pytest.fixture
    def repo_with_mocks(self, monkeypatch):
        repo = ModerationResultsRepository()
        redis_storage = AsyncMock()
        pg_storage = AsyncMock()
        monkeypatch.setattr(repo, "moderation_results_redis_storage", redis_storage)
        monkeypatch.setattr(repo, "moderation_results_postgres_storage", pg_storage)
        return repo, redis_storage, pg_storage

    @pytest.mark.asyncio
    async def test_select_cache_hit_does_not_call_db(self, repo_with_mocks):
        repo, redis_storage, pg_storage = repo_with_mocks
        redis_storage.get.return_value = MODERATION_RESULT_DATA

        result = await repo.select(TASK_ID)

        redis_storage.get.assert_called_once_with(TASK_ID)
        pg_storage.select.assert_not_called()
        assert isinstance(result, ModerationResultModel)
        assert result.id == TASK_ID

    @pytest.mark.asyncio
    async def test_select_cache_miss_calls_db(self, repo_with_mocks):
        repo, redis_storage, pg_storage = repo_with_mocks
        redis_storage.get.return_value = None
        pg_storage.select.return_value = MODERATION_RESULT_DATA

        result = await repo.select(TASK_ID)

        redis_storage.get.assert_called_once_with(TASK_ID)
        pg_storage.select.assert_called_once_with(TASK_ID)
        assert result.id == TASK_ID

    @pytest.mark.asyncio
    async def test_select_cache_miss_writes_result_to_cache(self, repo_with_mocks):
        repo, redis_storage, pg_storage = repo_with_mocks
        redis_storage.get.return_value = None
        pg_storage.select.return_value = MODERATION_RESULT_DATA

        await repo.select(TASK_ID)

        redis_storage.set.assert_called_once_with(TASK_ID, MODERATION_RESULT_DATA)

    @pytest.mark.asyncio
    async def test_update_writes_new_result_to_cache(self, repo_with_mocks):
        repo, redis_storage, pg_storage = repo_with_mocks
        pg_storage.update.return_value = MODERATION_RESULT_DATA

        await repo.update(TASK_ID, status="completed", is_violation=True, probability=0.9)

        redis_storage.set.assert_called_once_with(TASK_ID, MODERATION_RESULT_DATA)

    @pytest.mark.asyncio
    async def test_update_passes_correct_args_to_postgres(self, repo_with_mocks):
        repo, redis_storage, pg_storage = repo_with_mocks
        pg_storage.update.return_value = MODERATION_RESULT_DATA

        await repo.update(TASK_ID, status="completed")

        pg_storage.update.assert_called_once_with(TASK_ID, status="completed")


class TestModerationResultsRedisStorage:
    @pytest.fixture
    def storage(self):
        return ModerationResultsRedisStorage()

    @pytest.mark.asyncio
    async def test_get_returns_none_when_key_missing(self, storage, redis_mock):
        mock_connection, _ = redis_mock
        mock_connection.get.return_value = None

        result = await storage.get(TASK_ID)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_requests_correct_key(self, storage, redis_mock):
        mock_connection, _ = redis_mock
        mock_connection.get.return_value = None

        await storage.get(TASK_ID)

        mock_connection.get.assert_called_once_with(str(TASK_ID))

    @pytest.mark.asyncio
    async def test_get_returns_deserialized_dict(self, storage, redis_mock):
        mock_connection, _ = redis_mock
        serialized = json.dumps(
            {**MODERATION_RESULT_DATA, "created_at": "2026-01-01 12:00:00", "processed_at": "2026-01-01 12:01:00"}
        )
        mock_connection.get.return_value = serialized

        result = await storage.get(TASK_ID)

        assert result is not None
        assert result["id"] == TASK_ID
        assert result["status"] == "completed"
        assert result["is_violation"] is True
        assert result["probability"] == pytest.approx(0.9)

    @pytest.mark.asyncio
    async def test_set_uses_pipeline(self, storage, redis_mock):
        mock_connection, mock_pipeline = redis_mock

        await storage.set(TASK_ID, MODERATION_RESULT_DATA)

        mock_connection.pipeline.assert_called_once()
        mock_pipeline.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_stores_value_with_correct_key(self, storage, redis_mock):
        _, mock_pipeline = redis_mock

        await storage.set(TASK_ID, MODERATION_RESULT_DATA)

        mock_pipeline.set.assert_called_once()
        assert mock_pipeline.set.call_args.kwargs["name"] == str(TASK_ID)

    @pytest.mark.asyncio
    async def test_set_serializes_data_correctly(self, storage, redis_mock):
        _, mock_pipeline = redis_mock

        await storage.set(TASK_ID, MODERATION_RESULT_DATA)

        stored = json.loads(mock_pipeline.set.call_args.kwargs["value"])
        assert stored["id"] == TASK_ID
        assert stored["status"] == "completed"
        assert stored["is_violation"] is True

    @pytest.mark.asyncio
    async def test_set_applies_ttl_via_expire(self, storage, redis_mock):
        _, mock_pipeline = redis_mock

        await storage.set(TASK_ID, MODERATION_RESULT_DATA)

        mock_pipeline.expire.assert_called_once_with(str(TASK_ID), storage._TTL)

    @pytest.mark.asyncio
    async def test_storage_ttl_is_timedelta(self, storage):
        assert isinstance(storage._TTL, timedelta)
        assert storage._TTL.total_seconds() > 0
