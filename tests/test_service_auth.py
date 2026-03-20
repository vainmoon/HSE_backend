import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

import jwt

from services.auth import AuthService, hash_password, _SECRET_KEY, _ALGORITHM
from models.accounts import AccountModel
from errors import InvalidCredentialsError, AccountBlockedError, InvalidTokenError, AccountNotFoundError


def make_account(id: int = 1, login: str = "user", password: str = "pass", is_blocked: bool = False) -> AccountModel:
    return AccountModel(id=id, login=login, password=password, is_blocked=is_blocked)


def make_service(account: AccountModel | None = None, raises: Exception | None = None) -> AuthService:
    repo = MagicMock()
    if raises:
        repo.get_by_login_and_password = AsyncMock(side_effect=raises)
    else:
        repo.get_by_login_and_password = AsyncMock(return_value=account)
    return AuthService(account_repository=repo)


# --- hash_password ---

def test_hash_password_returns_md5_hex():
    import hashlib
    assert hash_password("secret") == hashlib.md5(b"secret").hexdigest()


def test_hash_password_same_input_same_output():
    assert hash_password("pass") == hash_password("pass")


def test_hash_password_different_inputs_differ():
    assert hash_password("pass1") != hash_password("pass2")


# --- register ---

@pytest.mark.asyncio
async def test_register_returns_account_model():
    account = make_account(id=10, login="newuser")
    repo = MagicMock()
    repo.create = AsyncMock(return_value=account)
    service = AuthService(account_repository=repo)

    result = await service.register("newuser", "pass")

    assert result.id == 10
    assert result.login == "newuser"


@pytest.mark.asyncio
async def test_register_passes_hashed_password_to_repo():
    repo = MagicMock()
    repo.create = AsyncMock(return_value=make_account())
    service = AuthService(account_repository=repo)

    await service.register("user", "mypassword")

    repo.create.assert_called_once_with("user", hash_password("mypassword"))


# --- login ---

@pytest.mark.asyncio
async def test_login_returns_token_for_valid_credentials():
    service = make_service(account=make_account())
    token = await service.login("user", "pass")
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_login_token_contains_correct_payload():
    account = make_account(id=42, login="alice")
    service = make_service(account=account)
    token = await service.login("alice", "pass")
    payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    assert payload["sub"] == "42"
    assert payload["login"] == "alice"
    assert payload["is_blocked"] is False


@pytest.mark.asyncio
async def test_login_passes_hashed_password_to_repo():
    repo = MagicMock()
    repo.get_by_login_and_password = AsyncMock(return_value=make_account())
    service = AuthService(account_repository=repo)

    await service.login("user", "mypassword")

    repo.get_by_login_and_password.assert_called_once_with("user", hash_password("mypassword"))


@pytest.mark.asyncio
async def test_login_raises_invalid_credentials_when_not_found():
    service = make_service(raises=AccountNotFoundError())
    with pytest.raises(InvalidCredentialsError):
        await service.login("nouser", "nopass")


@pytest.mark.asyncio
async def test_login_raises_account_blocked_when_is_blocked():
    service = make_service(account=make_account(is_blocked=True))
    with pytest.raises(AccountBlockedError):
        await service.login("user", "pass")


# --- verify_token ---

def test_verify_token_returns_account_model():
    service = make_service(account=make_account())
    account = make_account(id=7, login="bob")
    payload = {
        "sub": str(account.id),
        "login": account.login,
        "is_blocked": account.is_blocked,
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
    result = service.verify_token(token)
    assert result.id == 7
    assert result.login == "bob"
    assert result.is_blocked is False


def test_verify_token_raises_on_expired_token():
    service = make_service(account=make_account())
    payload = {
        "sub": 1,
        "login": "user",
        "is_blocked": False,
        "exp": datetime.now(tz=timezone.utc) - timedelta(seconds=1),
    }
    token = jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
    with pytest.raises(InvalidTokenError):
        service.verify_token(token)


def test_verify_token_raises_on_invalid_signature():
    service = make_service(account=make_account())
    payload = {
        "sub": 1,
        "login": "user",
        "is_blocked": False,
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, "wrong_secret", algorithm=_ALGORITHM)
    with pytest.raises(InvalidTokenError):
        service.verify_token(token)


def test_verify_token_raises_on_garbage_token():
    service = make_service(account=make_account())
    with pytest.raises(InvalidTokenError):
        service.verify_token("not.a.token")
