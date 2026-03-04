from pydantic import BaseModel, Field


class ItemModel(BaseModel):
    id: int = Field(ge=0)
    name: str = Field(min_length=1)
    description: str
    category: int = Field(ge=0)
    images_qty: int = Field(ge=0)
    seller_id: int = Field(ge=0)
    is_closed: bool = False


class ItemWithSellerModel(BaseModel):
    item_id: int = Field(ge=0)
    name: str = Field(min_length=1)
    description: str
    category: int = Field(ge=0)
    images_qty: int = Field(ge=0)
    seller_id: int = Field(ge=0)
    is_verified_seller: bool