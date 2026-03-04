import pytest
from datetime import datetime
from unittest.mock import AsyncMock

import routers.moderation
from clients.kafka import AsyncKafkaClient
from errors import ItemNotFoundError, ModerationResultNotFoundError
from workers.moderation_worker import MAX_RETRIES, process_message

from conftest import DummyModel

@pytest.fixture
def worker_deps():
    return (
        DummyModel(),   # model
        AsyncMock(),    # moderation_repo
        AsyncMock(),    # moderation_service
        AsyncMock(),    # kafka_client
    )

class TestAsyncPredict:
    def test_creates_task_returns_pending(self, app_client_with_kafka, monkeypatch):
        client, _ = app_client_with_kafka

        monkeypatch.setattr(
            routers.moderation.moderation_service,
            "send_moderation_request",
            AsyncMock(return_value={
                "id": 7, "status": "pending", "item_id": 42,
                "is_violation": None, "probability": None,
                "error_message": None, "created_at": datetime.now(), "processed_at": None,
            }),
        )

        response = client.post("/moderation/async_predict", json={"item_id": 42})

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == 7
        assert data["status"] == "pending"
        assert "message" in data

    def test_item_not_found_returns_404(self, app_client_with_kafka, monkeypatch):
        client, _ = app_client_with_kafka

        monkeypatch.setattr(
            routers.moderation.moderation_service,
            "send_moderation_request",
            AsyncMock(side_effect=ItemNotFoundError()),
        )

        response = client.post("/moderation/async_predict", json={"item_id": 999})

        assert response.status_code == 404

    def test_invalid_item_id_returns_422(self, app_client_with_kafka):
        client, _ = app_client_with_kafka

        response = client.post("/moderation/async_predict", json={"item_id": -1})

        assert response.status_code == 422


class TestModerationResult:
    def test_returns_pending_result(self, app_client_with_kafka, monkeypatch):
        client, _ = app_client_with_kafka

        monkeypatch.setattr(
            routers.moderation.moderation_service,
            "get_moderation_result",
            AsyncMock(return_value={
                "id": 3, "item_id": 5, "status": "pending",
                "is_violation": None, "probability": None,
                "error_message": None, "created_at": datetime.now(), "processed_at": None,
            }),
        )

        response = client.get("/moderation/moderation_result/3")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == 3
        assert data["status"] == "pending"
        assert data["is_violation"] is None
        assert data["probability"] is None

    def test_returns_completed_result(self, app_client_with_kafka, monkeypatch):
        client, _ = app_client_with_kafka

        monkeypatch.setattr(
            routers.moderation.moderation_service,
            "get_moderation_result",
            AsyncMock(return_value={
                "id": 5, "item_id": 10, "status": "completed",
                "is_violation": True, "probability": 0.9,
                "error_message": None, "created_at": datetime.now(), "processed_at": datetime.now(),
            }),
        )

        response = client.get("/moderation/moderation_result/5")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["is_violation"] is True
        assert data["probability"] == pytest.approx(0.9)

    def test_task_not_found_returns_404(self, app_client_with_kafka, monkeypatch):
        client, _ = app_client_with_kafka

        monkeypatch.setattr(
            routers.moderation.moderation_service,
            "get_moderation_result",
            AsyncMock(side_effect=ModerationResultNotFoundError()),
        )

        response = client.get("/moderation/moderation_result/999")

        assert response.status_code == 404


class TestWorkerProcessMessage:
    @pytest.mark.asyncio
    async def test_success_updates_completed(self, worker_deps, monkeypatch):
        model, moderation_repo, moderation_service, kafka_client = worker_deps
        monkeypatch.setattr("workers.moderation_worker.RETRY_DELAY", 0)
        moderation_service.moderate_item_by_id.return_value = (1, 0.95)

        data = {"task_id": 1, "item_id": 42, "timestamp": "2026-01-01T00:00:00"}
        await process_message(data, model, moderation_repo, moderation_service, kafka_client)

        moderation_repo.update.assert_called_once()
        kwargs = moderation_repo.update.call_args
        assert kwargs.args[0] == 1
        assert kwargs.kwargs["status"] == "completed"
        assert kwargs.kwargs["is_violation"] is True
        assert kwargs.kwargs["probability"] == pytest.approx(0.95)
        kafka_client.send_to_dlq.assert_not_called()

    @pytest.mark.asyncio
    async def test_success_no_violation(self, worker_deps, monkeypatch):
        model, moderation_repo, moderation_service, kafka_client = worker_deps
        monkeypatch.setattr("workers.moderation_worker.RETRY_DELAY", 0)
        moderation_service.moderate_item_by_id.return_value = (0, 0.1)

        data = {"task_id": 2, "item_id": 10, "timestamp": "2026-01-01T00:00:00"}
        await process_message(data, model, moderation_repo, moderation_service, kafka_client)

        assert moderation_repo.update.call_args.kwargs["status"] == "completed"
        assert moderation_repo.update.call_args.kwargs["is_violation"] is False
        kafka_client.send_to_dlq.assert_not_called()

    @pytest.mark.asyncio
    async def test_retries_up_to_max_on_failure(self, worker_deps, monkeypatch):
        model, moderation_repo, moderation_service, kafka_client = worker_deps
        monkeypatch.setattr("workers.moderation_worker.RETRY_DELAY", 0)
        moderation_service.moderate_item_by_id.side_effect = Exception("ML service down")

        data = {"task_id": 3, "item_id": 99, "timestamp": "2026-01-01T00:00:00"}
        await process_message(data, model, moderation_repo, moderation_service, kafka_client)

        assert moderation_service.moderate_item_by_id.call_count == MAX_RETRIES

    @pytest.mark.asyncio
    async def test_success_on_third_attempt(self, worker_deps, monkeypatch):
        model, moderation_repo, moderation_service, kafka_client = worker_deps
        monkeypatch.setattr("workers.moderation_worker.RETRY_DELAY", 0)
        moderation_service.moderate_item_by_id.side_effect = [
            Exception("transient"),
            Exception("transient"),
            (0, 0.3),
        ]

        data = {"task_id": 4, "item_id": 15, "timestamp": "2026-01-01T00:00:00"}
        await process_message(data, model, moderation_repo, moderation_service, kafka_client)

        assert moderation_service.moderate_item_by_id.call_count == 3
        assert moderation_repo.update.call_args.kwargs["status"] == "completed"
        kafka_client.send_to_dlq.assert_not_called()


class TestDLQ:
    @pytest.mark.asyncio
    async def test_sends_to_dlq_after_all_retries(self, worker_deps, monkeypatch):
        model, moderation_repo, moderation_service, kafka_client = worker_deps
        monkeypatch.setattr("workers.moderation_worker.RETRY_DELAY", 0)
        moderation_service.moderate_item_by_id.side_effect = Exception("inference failed")

        data = {"task_id": 5, "item_id": 7, "timestamp": "2026-01-01T00:00:00"}
        await process_message(data, model, moderation_repo, moderation_service, kafka_client)

        kafka_client.send_to_dlq.assert_called_once()
        sent_data, sent_error = kafka_client.send_to_dlq.call_args.args
        assert sent_data == data
        assert "inference failed" in sent_error

    @pytest.mark.asyncio
    async def test_failed_status_set_before_dlq(self, worker_deps, monkeypatch):
        model, moderation_repo, moderation_service, kafka_client = worker_deps
        monkeypatch.setattr("workers.moderation_worker.RETRY_DELAY", 0)
        moderation_service.moderate_item_by_id.side_effect = Exception("error")

        data = {"task_id": 6, "item_id": 8, "timestamp": "2026-01-01T00:00:00"}
        await process_message(data, model, moderation_repo, moderation_service, kafka_client)

        moderation_repo.update.assert_called_once()
        assert moderation_repo.update.call_args.kwargs["status"] == "failed"
        assert moderation_repo.update.call_args.kwargs["error_message"] == "error"

    @pytest.mark.asyncio
    async def test_dlq_message_contains_required_fields(self):
        kafka = AsyncKafkaClient.__new__(AsyncKafkaClient)
        kafka.producer = AsyncMock()

        original = {"task_id": 1, "item_id": 2, "timestamp": "2026-01-01T00:00:00"}
        await kafka.send_to_dlq(original, "some error", retry_count=3)

        call_args = kafka.producer.send_and_wait.call_args
        assert call_args.args[0] == "moderation_dlq"
        dlq_msg = call_args.kwargs["value"]
        assert dlq_msg["original_message"] == original
        assert dlq_msg["error"] == "some error"
        assert "timestamp" in dlq_msg
        assert dlq_msg["retry_count"] == 3

    @pytest.mark.asyncio
    async def test_dlq_retry_count_equals_max_retries(self, worker_deps, monkeypatch):
        model, moderation_repo, moderation_service, kafka_client = worker_deps
        monkeypatch.setattr("workers.moderation_worker.RETRY_DELAY", 0)
        moderation_service.moderate_item_by_id.side_effect = Exception("error")

        data = {"task_id": 1, "item_id": 2, "timestamp": "2026-01-01T00:00:00"}
        await process_message(data, model, moderation_repo, moderation_service, kafka_client)

        assert kafka_client.send_to_dlq.call_args.kwargs["retry_count"] == MAX_RETRIES


class TestCloseItem:
    def test_close_item_returns_204(self, app_client_with_kafka, monkeypatch):
        client, _ = app_client_with_kafka

        monkeypatch.setattr(
            routers.moderation.moderation_service,
            "close_item",
            AsyncMock(return_value=None),
        )

        response = client.post("/moderation/close", json={"item_id": 1})

        assert response.status_code == 204

    def test_close_item_not_found_returns_404(self, app_client_with_kafka, monkeypatch):
        client, _ = app_client_with_kafka

        monkeypatch.setattr(
            routers.moderation.moderation_service,
            "close_item",
            AsyncMock(side_effect=ItemNotFoundError()),
        )

        response = client.post("/moderation/close", json={"item_id": 999})

        assert response.status_code == 404

    def test_close_item_invalid_item_id_returns_422(self, app_client_with_kafka):
        client, _ = app_client_with_kafka

        response = client.post("/moderation/close", json={"item_id": -1})

        assert response.status_code == 422
