from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from decimal import Decimal

class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    image_url: str | None = None
    price: Decimal
    stock_quantity: int = 0
    category_id: uuid.UUID

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    image_url: str | None = None
    price: Decimal
    stock_quantity: int
    category_id: uuid.UUID
    created_at: datetime

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    image_url: str | None = None
    price: Decimal | None = None
    stock_quantity: int | None = None
    category_id: uuid.UUID | None = None

class ProductListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[ProductResponse]