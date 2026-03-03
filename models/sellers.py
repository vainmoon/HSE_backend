from pydantic import BaseModel, Field


class SellerModel(BaseModel):
    id: int = Field(ge=0)
    is_verified_seller: bool