import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cart.models import CartItem
from app.modules.cart.service import get_or_create_cart
from app.modules.products.models import Product
from app.modules.orders.models import Order, OrderItem, OrderStatus


class EmptyCartError(Exception):
    pass


class InsufficientStockError(Exception):
    def __init__(self, product_name: str, available: int, requested: int):
        self.product_name = product_name
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient stock for '{product_name}': requested {requested}, available {available}"
        )


async def create_order_from_cart(db: AsyncSession, user_id: uuid.UUID) -> Order:
    cart = await get_or_create_cart(db, user_id)

    result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
    cart_items = result.scalars().all()

    if not cart_items:
        raise EmptyCartError()

    order_items: list[OrderItem] = []
    total = Decimal("0")

    for cart_item in cart_items:
        # Row-level lock: blocks concurrent orders on the SAME product
        # until this transaction commits or rolls back.
        product_result = await db.execute(
            select(Product).where(Product.id == cart_item.product_id).with_for_update()
        )
        product = product_result.scalar_one_or_none()

        if product is None:
            raise InsufficientStockError("unknown product", 0, cart_item.quantity)

        if product.stock_quantity < cart_item.quantity:
            raise InsufficientStockError(product.name, product.stock_quantity, cart_item.quantity)

        product.stock_quantity -= cart_item.quantity

        order_items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                unit_price=Decimal(str(product.price)),
                quantity=cart_item.quantity,
            )
        )
        total += Decimal(str(product.price)) * cart_item.quantity

    order = Order(user_id=user_id, status=OrderStatus.PENDING, total=total, items=order_items)
    db.add(order)

    for cart_item in cart_items:
        await db.delete(cart_item)

    await db.commit()
    await db.refresh(order, attribute_names=["items"])
    return order