import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from routers.moderation import ModerateItemInDto
from main import app
from services.moderation import ModerationService
from dependencies import get_current_account
from models.accounts import AccountModel


class DummyModel:
    pass


def _mock_account() -> AccountModel:
    return AccountModel(id=1, login="testuser", password="", is_blocked=False)


@pytest.fixture
def app_client():
    app.dependency_overrides[get_current_account] = _mock_account
    app.state.model = DummyModel()
    with TestClient(app) as client:
        yield client
    app.state.model = None
    app.dependency_overrides.pop(get_current_account, None)


@pytest.fixture
def mock_kafka():
    return AsyncMock()


@pytest.fixture
def app_client_with_kafka(monkeypatch, mock_kafka):
    app.dependency_overrides[get_current_account] = _mock_account
    monkeypatch.setattr("main.AsyncKafkaClient", lambda: mock_kafka)
    app.state.model = DummyModel()
    with TestClient(app) as client:
        yield client, mock_kafka
    app.state.model = None
    app.dependency_overrides.pop(get_current_account, None)


@pytest.fixture
def valid_item() -> ModerateItemInDto:
    return ModerateItemInDto(
        seller_id=1,
        is_verified_seller=True,
        item_id=2,
        name="valid item",
        description="valid item",
        category=3,
        images_qty=4,
    )


@pytest.fixture
def moderation_service() -> ModerationService:
    return ModerationService()


@pytest.fixture
def redis_mock(monkeypatch):
    mock_connection = AsyncMock()
    mock_pipeline = MagicMock()
    mock_pipeline.execute = AsyncMock()
    mock_connection.pipeline = MagicMock(return_value=mock_pipeline)

    @asynccontextmanager
    async def fake_get_redis_connection():
        yield mock_connection

    monkeypatch.setattr(
        "repositories.moderation_results.get_redis_connection",
        fake_get_redis_connection,
    )

    return mock_connection, mock_pipeline


pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def anyio_backend():
    return "asyncio"

