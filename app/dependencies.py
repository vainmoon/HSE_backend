from fastapi import Request

from errors import InvalidTokenError
from models.accounts import AccountModel
from services.auth import AuthService

_auth_service = AuthService()


def get_model(request: Request):
    return request.app.state.model


def get_kafka_client(request: Request):
    return request.app.state.kafka_client


def get_current_account(request: Request) -> AccountModel:
    token = request.cookies.get("access_token")
    if not token:
        raise InvalidTokenError("Missing access token")
    return _auth_service.verify_token(token)