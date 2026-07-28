import uuid
from decimal import Decimal
from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    product_price: Decimal
    quantity: int

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    items: list[CartItemResponse]
    subtotal: Decimal

    class Config:
        from_attributes = True