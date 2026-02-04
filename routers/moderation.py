from fastapi import APIRouter, Depends
from pydantic import BaseModel
import logging

from services.moderation import ModerationService
from dependencies import get_model

logger = logging.getLogger(__name__)

class ModerateItemInDto(BaseModel):
    seller_id: int
    is_verified_seller: bool
    item_id: int
    name: str
    description: str
    category: int
    images_qty: int


class ModerateItemOutDto(BaseModel):
    is_violation: bool
    probability: float


router = APIRouter()

moderation_service = ModerationService()


@router.post('/predict')
async def moderate_item(dto: ModerateItemInDto, model=Depends(get_model)) -> ModerateItemOutDto:
    logger.info("Moderation request: %s", dto.model_dump())

    data = dto.model_dump()
    pred, confidence = moderation_service.moderate_item(model, data)
    logger.info("Moderation result: is_violation=%s, probability=%s", pred, confidence)
    
    return ModerateItemOutDto(is_violation=pred, probability=confidence)