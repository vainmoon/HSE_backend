import pytest
from services.moderation import ModerationService


@pytest.mark.parametrize(
    'is_verified_seller, images_qty, result',
    [(True, 0, True), (True, 1, True), (False, 0, False), (False, 1, True)],
)
def test_moderate_item(
    moderation_service: ModerationService,
    is_verified_seller: bool,
    images_qty: int,
    result: bool,
):
    assert moderation_service.moderate_item(is_verified_seller, images_qty) == result
