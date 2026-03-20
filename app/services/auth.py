import hashlib
import os
from datetime import datetime, timezone, timedelta

import jwt

from errors import AccountNotFoundError, InvalidCredentialsError, AccountBlockedError, InvalidTokenError
from models.accounts import AccountModel
from repositories.accounts import AccountRepository

def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()


_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "secret")
_ALGORITHM = "HS256"
_TOKEN_TTL = timedelta(hours=int(os.getenv("JWT_TTL_HOURS", "24")))


class AuthService:
    def __init__(self, account_repository: AccountRepository | None = None):
        self._repo = account_repository or AccountRepository()

    async def register(self, login: str, password: str) -> AccountModel:
        return await self._repo.create(login, hash_password(password))

    async def login(self, login: str, password: str) -> str:
        try:
            account = await self._repo.get_by_login_and_password(login, hash_password(password))
        except AccountNotFoundError:
            raise InvalidCredentialsError()

        if account.is_blocked:
            raise AccountBlockedError()

        return self._issue_token(account)

    def verify_token(self, token: str) -> AccountModel:
        try:
            payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Token is invalid")

        return AccountModel(
            id=payload["sub"],
            login=payload["login"],
            password="",
            is_blocked=payload["is_blocked"],
        )

    def _issue_token(self, account: AccountModel) -> str:
        payload = {
            "sub": account.id,
            "login": account.login,
            "is_blocked": account.is_blocked,
            "exp": datetime.now(tz=timezone.utc) + _TOKEN_TTL,
        }
        return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)
