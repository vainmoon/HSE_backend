from pydantic import BaseModel


class SellerModel(BaseModel):
    id: int
    is_verified_seller: bool