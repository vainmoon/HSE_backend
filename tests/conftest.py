import pytest
from fastapi.testclient import TestClient
from routers.moderation import ModerateItemInDto
from main import app
from services.moderation import ModerationService


class DummyModel:
    pass


@pytest.fixture
def app_client():
    app.state.model = DummyModel()
    client = TestClient(app)
    yield client
    app.state.model = None


@pytest.fixture
def valid_item() -> ModerateItemInDto:
    return ModerateItemInDto(
        seller_id=1,
        is_verified_seller=True,
        item_id=2,
        name='valid item',
        description='valid item',
        category=3,
        images_qty=4,
    )


@pytest.fixture
def moderation_service() -> ModerationService:
    return ModerationService()
