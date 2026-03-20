from pydantic import BaseModel, Field


class AccountModel(BaseModel):
    id: int = Field(ge=0)
    login: str
    password: str
    is_blocked: bool
