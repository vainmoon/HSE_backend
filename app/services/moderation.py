from model import predict
from errors import ModelUnavailableError, InferenceError
from repositories.items import ItemRepository
from repositories.sellers import SellerRepository
from repositories.moderation_results import ModerationResultsRepository

class ModerationService:
    def __init__(self):
        self.item_repo = ItemRepository()
        self.seller_repo = SellerRepository()
        self.moderation_results_repo = ModerationResultsRepository()

    def moderate_item(self, model, moderate_item: dict):
        if model is None:
            raise ModelUnavailableError

        try:
            pred, confidence = predict(model, moderate_item)
            return pred, confidence

        except Exception as e:
            raise InferenceError(e)

    async def moderate_item_by_id(self, model, item_id: int):
        features = await self.item_repo.get_with_seller(item_id)

        return self.moderate_item(model, features.model_dump())
    
    async def send_moderation_request(self, kafka_client, item_id: int) -> int:
        await self.item_repo.get(item_id)

        task = await self.moderation_results_repo.create(item_id)

        await kafka_client.send_moderation_request(item_id)

        return task.model_dump()