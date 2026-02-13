from model import predict
from errors import ModelUnavailableError, InferenceError
from repositories.items import ItemRepository
from repositories.sellers import SellerRepository


class ModerationService:
    def __init__(self):
        self.item_repo = ItemRepository()
        self.seller_repo = SellerRepository()

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