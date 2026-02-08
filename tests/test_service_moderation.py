import pytest
from services.moderation import ModerationService
from errors import ModelUnavailableError


@pytest.fixture
def service():
    return ModerationService()


@pytest.fixture
def service_factory(monkeypatch):
    def _factory(pred: bool, prob: float):
        def fake_predict(model, data):
            return pred, prob

        monkeypatch.setattr("services.moderation.predict", fake_predict)
        return ModerationService()

    return _factory


def test_violation_true(service_factory):
    service = service_factory(pred=True, prob=0.9)
    pred, prob = service.moderate_item(model=object(), moderate_item={})
    assert pred is True


def test_violation_false(service_factory):
    service = service_factory(pred=False, prob=0.1)
    pred, prob = service.moderate_item(model=object(), moderate_item={})
    assert pred is False


def test_model_unavailable(service):
    with pytest.raises(ModelUnavailableError):
        service.moderate_item(model=None, moderate_item={})
