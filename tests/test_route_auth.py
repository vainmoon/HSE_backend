import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from models.accounts import AccountModel
from errors import InvalidCredentialsError, AccountBlockedError


@pytest.fixture
def mock_auth_service():
    with patch("routers.auth.auth_service") as mock:
        yield mock


def test_register_success_returns_account(app_client: TestClient, mock_auth_service):
    mock_auth_service.register = AsyncMock(return_value=AccountModel(
        id=1, login="newuser", password="hashed", is_blocked=False
    ))

    response = app_client.post("/auth/register", json={"login": "newuser", "password": "pass"})

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["login"] == "newuser"
    assert body["is_blocked"] is False
    assert "password" not in body


@pytest.mark.parametrize("payload", [
    {"login": "", "password": "pass"},
    {"login": "user", "password": ""},
    {"password": "pass"},
    {"login": "user"},
    {},
])
def test_register_invalid_body_returns_422(app_client: TestClient, payload: dict):
    response = app_client.post("/auth/register", json=payload)
    assert response.status_code == 422


def test_login_success_sets_cookie(app_client: TestClient, mock_auth_service):
    mock_auth_service.login = AsyncMock(return_value="test.jwt.token")

    response = app_client.post("/auth/login", json={"login": "user", "password": "pass"})

    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert response.cookies["access_token"] == "test.jwt.token"


def test_login_invalid_credentials_returns_401(app_client: TestClient, mock_auth_service):
    mock_auth_service.login = AsyncMock(side_effect=InvalidCredentialsError())

    response = app_client.post("/auth/login", json={"login": "nouser", "password": "nopass"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid login or password"


def test_login_blocked_account_returns_403(app_client: TestClient, mock_auth_service):
    mock_auth_service.login = AsyncMock(side_effect=AccountBlockedError())

    response = app_client.post("/auth/login", json={"login": "blocked", "password": "pass"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is blocked"


@pytest.mark.parametrize("payload", [
    {"login": "", "password": "pass"},
    {"login": "user", "password": ""},
    {"login": "", "password": ""},
    {"password": "pass"},
    {"login": "user"},
    {},
])
def test_login_invalid_body_returns_422(app_client: TestClient, payload: dict):
    response = app_client.post("/auth/login", json=payload)
    assert response.status_code == 422
