import pytest
from fastapi.testclient import TestClient
from routers.moderation import ModerateItemInDto


@pytest.mark.parametrize(
    "invalid_field, invalid_value",
    [
        ("seller_id", -3),
        ("is_verified_seller", 4),
        ("item_id", -4),
        ("name", ""),
        ("description", ""),
        ("category", -6),
        ("images_qty", -2),
    ],
)
def test_invalid_item(
    app_client: TestClient,
    valid_item: ModerateItemInDto,
    invalid_field: str,
    invalid_value,
):
    invalid_item = valid_item.model_dump()
    invalid_item[invalid_field] = invalid_value
    response = app_client.post("/moderation/predict", json=invalid_item)
    assert response.status_code == 422
