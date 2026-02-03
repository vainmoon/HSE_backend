class ModerationService:
    def moderate_item(self, is_verified_seller: bool, images_qty: int) -> bool:
        return is_verified_seller or images_qty > 0
