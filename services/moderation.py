from model import predict
from errors import ModelUnavailableError, InferenceError
from repositories.items import ItemRepository
from repositories.sellers import SellerRepository
from repositories.moderation_results import ModerationResultRepository
from models.moderation_results import ModerationResultModel


class ModerationService:
    def __init__(self):
        self.item_repo = ItemRepository()
        self.seller_repo = SellerRepository()
        self.moderation_result_repo = ModerationResultRepository()

    def moderate_item(self, model, moderate_item: dict):
        if model is None:
            raise ModelUnavailableError

        try:
            pred, confidence = predict(model, moderate_item)
            return pred, confidence

        except Exception as e:
            raise InferenceError(e)

    async def moderate_item_by_id(self, model, moderate_item_by_id: dict):
        item = await self.item_repo.get(moderate_item_by_id['item_id'])

        seller = await self.seller_repo.get(item.seller_id)

        features = {
            "seller_id": seller.id,
            "is_verified_seller": seller.is_verified_seller,
            "item_id": item.id,
            "name": item.name,
            "description": item.description,
            "category": item.category,
            "images_qty": item.images_qty,
        }

        return self.moderate_item(model, features)

    async def get_moderation_result(self, task_id: int) -> ModerationResultModel:
        return await self.moderation_result_repo.get_by_id(task_id)

    async def create_async_predict(self, kafka_client, item_id: int) -> ModerationResultModel:
        await self.item_repo.get(item_id)

        result = await self.moderation_result_repo.create_pending(item_id)

        await kafka_client.send_moderation_request(result.id, item_id)

        return result