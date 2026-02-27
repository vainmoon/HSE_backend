import pytest
from datetime import datetime, timezone
from typing import Optional
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from errors import ItemNotFoundError, ModerationResultNotFoundError
from models.moderation_results import ModerationResultModel


def _make_result(
    task_id: int = 1,
    item_id: int = 1,
    status: str = 'pending',
    is_violation: Optional[bool] = None,
    probability: Optional[float] = None,
) -> ModerationResultModel:
    return ModerationResultModel(
        id=task_id,
        item_id=item_id,
        status=status,
        is_violation=is_violation,
        probability=probability,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        processed_at=None,
    )


class TestAsyncPredict:
    def test_success(self, app_client: TestClient):
        pending = _make_result(task_id=1, item_id=1)

        with patch(
            'routers.moderation.moderation_service.create_async_predict',
            new=AsyncMock(return_value=pending),
        ):
            response = app_client.post('/moderation/async_predict', json={'item_id': 1})

        assert response.status_code == 200
        data = response.json()
        assert data['task_id'] == 1
        assert data['status'] == 'pending'
        assert data['message'] == 'Moderation request accepted'

    def test_item_not_found(self, app_client: TestClient):
        with patch(
            'routers.moderation.moderation_service.create_async_predict',
            new=AsyncMock(side_effect=ItemNotFoundError()),
        ):
            response = app_client.post('/moderation/async_predict', json={'item_id': 999})

        assert response.status_code == 404

    def test_invalid_item_id(self, app_client: TestClient):
        response = app_client.post('/moderation/async_predict', json={'item_id': -1})
        assert response.status_code == 422


class TestModerationResult:
    def test_get_pending(self, app_client: TestClient):
        pending = _make_result(task_id=5, status='pending')

        with patch(
            'routers.moderation.moderation_service.get_moderation_result',
            new=AsyncMock(return_value=pending),
        ):
            response = app_client.get('/moderation/moderation_result/5')

        assert response.status_code == 200
        data = response.json()
        assert data['task_id'] == 5
        assert data['status'] == 'pending'
        assert data['is_violation'] is None
        assert data['probability'] is None

    def test_get_completed(self, app_client: TestClient):
        completed = _make_result(
            task_id=5, status='completed', is_violation=True, probability=0.87
        )

        with patch(
            'routers.moderation.moderation_service.get_moderation_result',
            new=AsyncMock(return_value=completed),
        ):
            response = app_client.get('/moderation/moderation_result/5')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'completed'
        assert data['is_violation'] is True
        assert data['probability'] == pytest.approx(0.87)

    def test_not_found(self, app_client: TestClient):
        with patch(
            'routers.moderation.moderation_service.get_moderation_result',
            new=AsyncMock(side_effect=ModerationResultNotFoundError()),
        ):
            response = app_client.get('/moderation/moderation_result/999')

        assert response.status_code == 404
