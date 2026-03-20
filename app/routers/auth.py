from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from errors import InvalidCredentialsError, AccountBlockedError
from services.auth import AuthService

router = APIRouter()

auth_service = AuthService()

_COOKIE_NAME = "access_token"


class LoginInDto(BaseModel):
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)


@router.post("/login", status_code=200)
async def login(dto: LoginInDto, response: Response) -> None:
    token = await auth_service.login(dto.login, dto.password)
    response.set_cookie(key=_COOKIE_NAME, value=token, httponly=True)
