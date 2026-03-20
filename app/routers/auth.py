from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from errors import InvalidCredentialsError, AccountBlockedError
from models.accounts import AccountModel
from services.auth import AuthService

router = APIRouter()

auth_service = AuthService()

_COOKIE_NAME = "access_token"


class LoginInDto(BaseModel):
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AccountOutDto(BaseModel):
    id: int
    login: str
    is_blocked: bool


@router.post("/register", status_code=201)
async def register(dto: LoginInDto) -> AccountOutDto:
    account = await auth_service.register(dto.login, dto.password)
    return AccountOutDto(id=account.id, login=account.login, is_blocked=account.is_blocked)


@router.post("/login", status_code=200)
async def login(dto: LoginInDto, response: Response) -> None:
    token = await auth_service.login(dto.login, dto.password)
    response.set_cookie(key=_COOKIE_NAME, value=token, httponly=True)
