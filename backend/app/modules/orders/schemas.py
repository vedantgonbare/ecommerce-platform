import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.modules.orders.models import OrderStatus


class OrderItemResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    unit_price: Decimal
    quantity: int

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: uuid.UUID
    status: OrderStatus
    total: Decimal
    created_at: datetime
    items: list[OrderItemResponse]

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[OrderResponse]