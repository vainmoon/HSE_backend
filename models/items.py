from pydantic import BaseModel


class ItemModel(BaseModel):
    id: int
    name: str
    description: str
    category: int
    images_qty: int
    seller_id: int