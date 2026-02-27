from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ModerationResultModel(BaseModel):
    id: int
    item_id: int
    status: str
    is_violation: Optional[bool]
    probability: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
