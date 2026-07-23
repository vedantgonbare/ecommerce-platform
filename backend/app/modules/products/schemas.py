from pydantic import BaseModel
import uuid
from datetime import datetime
from decimal import Decimal

class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    stock_quantity: int = 0
    category_id: uuid.UUID

class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price: Decimal
    stock_quantity: int
    category_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    stock_quantity: int | None = None
    category_id: uuid.UUID | None = None
