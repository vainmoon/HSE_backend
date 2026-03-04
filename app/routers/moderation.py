from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
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

class ModerateTaskInfoOutDto(BaseModel):
    task_id: int = Field(ge=0)
    status: str
    message: str

class ModerateTaskResultOutDto(BaseModel):
    task_id: int = Field(ge=0)
    status: str
    is_violation: bool | None
    probability: float | None

class CloseItemInDto(BaseModel):
    item_id: int = Field(ge=0)

router = APIRouter()

moderation_service = ModerationService()


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
    pred, confidence = await moderation_service.moderate_item_by_id(model, data["item_id"])
    logger.info("Simple moderation result: is_violation=%s, probability=%s", pred, confidence)

    return ModerateItemOutDto(is_violation=pred, probability=confidence)

@router.post("/async_predict")
async def async_predict(
    dto: ModerateItemByIdInDto,
    kafka_client=Depends(get_kafka_client)
) -> ModerateTaskInfoOutDto:
    logger.info("Async moderation request: %s", dto.model_dump())
    data = dto.model_dump()
    
    tas_info = await moderation_service.send_moderation_request(kafka_client, data["item_id"])

    return ModerateTaskInfoOutDto(
        task_id=tas_info["id"],
        status=tas_info["status"],
        message="Moderation request accepted."
    )

@router.post("/close", status_code=204)
async def close_item(dto: CloseItemInDto) -> None:
    logger.info("Close item request: %s", dto.model_dump())
    await moderation_service.close_item(dto.item_id)


@router.get("/moderation_result/{task_id}")
async def get_moderation_result(task_id: int) -> ModerateTaskResultOutDto:
    logger.info("Getting moderation result for task_id: %s", task_id)

    task_result = await moderation_service.get_moderation_result(task_id)

    return ModerateTaskResultOutDto(
        task_id=task_id,
        status=task_result["status"],
        is_violation=task_result["is_violation"],
        probability=task_result["probability"]
    )