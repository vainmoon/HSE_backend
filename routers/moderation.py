from fastapi import APIRouter
from pydantic import BaseModel
from services.moderation import ModerationService


class ModerateItemInDto(BaseModel):
    seller_id: int
    is_verified_seller: bool
    item_id: int
    name: str
    description: str
    category: int
    images_qty: int


class ModerateItemOutDto(BaseModel):
    approved: bool


router = APIRouter()

moderation_service = ModerationService()


@router.post('/predict')
async def moderate_item(dto: ModerateItemInDto) -> ModerateItemOutDto:
    result = moderation_service.moderate_item(dto.is_verified_seller, dto.images_qty)
    return ModerateItemOutDto(approved=result)
