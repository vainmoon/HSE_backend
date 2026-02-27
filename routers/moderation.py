from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
import logging

from services.moderation import ModerationService
from dependencies import get_model, get_kafka_client

logger = logging.getLogger(__name__)


class ModerateItemInDto(BaseModel):
    seller_id: int = Field(ge=0)
    is_verified_seller: bool
    item_id: int = Field(ge=0)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: int = Field(ge=0)
    images_qty: int = Field(ge=0)

class ModerateItemByIdInDto(BaseModel):
    item_id: int = Field(ge=0)

class ModerateItemOutDto(BaseModel):
    is_violation: bool
    probability: float


router = APIRouter()

moderation_service = ModerationService()


class AsyncPredictInDto(BaseModel):
    item_id: int = Field(ge=0)


class AsyncPredictOutDto(BaseModel):
    task_id: int
    status: str
    message: str


class ModerationResultOutDto(BaseModel):
    task_id: int
    status: str
    is_violation: Optional[bool]
    probability: Optional[float]


@router.post("/async_predict")
async def async_predict(
    dto: AsyncPredictInDto,
    kafka_client=Depends(get_kafka_client),
) -> AsyncPredictOutDto:
    logger.info("Async moderation request: item_id=%s", dto.item_id)

    result = await moderation_service.create_async_predict(kafka_client, dto.item_id)

    logger.info("Async moderation task created: task_id=%s", result.id)

    return AsyncPredictOutDto(
        task_id=result.id,
        status="pending",
        message="Moderation request accepted",
    )


@router.get("/moderation_result/{task_id}")
async def get_moderation_result(task_id: int) -> ModerationResultOutDto:
    logger.info("Moderation result request: task_id=%s", task_id)

    result = await moderation_service.get_moderation_result(task_id)

    return ModerationResultOutDto(
        task_id=result.id,
        status=result.status,
        is_violation=result.is_violation,
        probability=result.probability,
    )


@router.post("/predict")
async def moderate_item(
    dto: ModerateItemInDto, model=Depends(get_model)
) -> ModerateItemOutDto:
    logger.info("Moderation request: %s", dto.model_dump())

    data = dto.model_dump()
    pred, confidence = moderation_service.moderate_item(model, data)
    logger.info("Moderation result: is_violation=%s, probability=%s", pred, confidence)

    return ModerateItemOutDto(is_violation=pred, probability=confidence)


@router.post("/simple_predict")
async def simple_predict(
    dto: ModerateItemByIdInDto, model=Depends(get_model)
) -> ModerateItemOutDto:
    logger.info("Simple moderation request: %s", dto.model_dump())

    data = dto.model_dump()
    pred, confidence = await moderation_service.moderate_item_by_id(model, data)
    logger.info("Simple moderation result: is_violation=%s, probability=%s", pred, confidence)

    return ModerateItemOutDto(is_violation=pred, probability=confidence)
