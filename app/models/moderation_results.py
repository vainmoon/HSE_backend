from datetime import datetime
from pydantic import BaseModel, Field


class ModerationResultModel(BaseModel):
    id: int = Field(ge=0)
    item_id: int = Field(ge=0)
    status: str
    is_violation: bool | None
    probability: float | None
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None