import pytest
from unittest.mock import MagicMock, patch

from fastapi import Request

from dependencies import get_current_account
from errors import InvalidTokenError
from models.accounts import AccountModel


def make_request(cookie_value: str | None) -> Request:
    scope = {"type": "http", "headers": []}
    request = Request(scope)
    if cookie_value is not None:
        request._cookies = {"access_token": cookie_value}
    else:
        request._cookies = {}
    return request


def make_account(id: int = 1, login: str = "user") -> AccountModel:
    return AccountModel(id=id, login=login, password="pass", is_blocked=False)


def test_returns_account_when_token_is_valid():
    account = make_account(id=5, login="alice")
    with patch("dependencies._auth_service") as mock_service:
        mock_service.verify_token = MagicMock(return_value=account)
        result = get_current_account(make_request("valid.jwt.token"))

    assert result.id == 5
    assert result.login == "alice"
    mock_service.verify_token.assert_called_once_with("valid.jwt.token")


def test_raises_when_cookie_is_missing():
    with pytest.raises(InvalidTokenError):
        get_current_account(make_request(None))


def test_raises_when_token_is_invalid():
    with patch("dependencies._auth_service") as mock_service:
        mock_service.verify_token = MagicMock(side_effect=InvalidTokenError("Token is invalid"))
        with pytest.raises(InvalidTokenError):
            get_current_account(make_request("bad.token"))
