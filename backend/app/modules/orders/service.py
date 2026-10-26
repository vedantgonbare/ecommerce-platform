import uuid
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.cart.models import CartItem
from app.modules.cart.service import get_or_create_cart
from app.modules.products.models import Product
from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.orders.tasks import send_order_confirmation

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

    send_order_confirmation.delay(str(order.id))
    
    return order


class OrderNotFoundError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    def __init__(self, current_status: OrderStatus):
        self.current_status = current_status
        super().__init__(f"Cannot cancel an order with status '{current_status.value}'")


async def list_orders(db: AsyncSession, user_id: uuid.UUID, limit: int = 20, offset: int = 0):
    base_query = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())

    count_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(
        base_query.options(selectinload(Order.items)).limit(limit).offset(offset)
    )
    orders = result.scalars().all()

    return total, orders


async def get_order_or_404(
    db: AsyncSession,
    user_id: uuid.UUID,
    order_id: uuid.UUID,
    *,
    for_update: bool = False,
) -> Order:
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    if for_update:
        query = query.with_for_update(of=Order)

    result = await db.execute(query)
    order = result.scalar_one_or_none()
    if order is None:
        raise OrderNotFoundError()
    return order


async def cancel_order(db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    # 1. Lock the ORDER row first, so a double-click's second request waits here
    order = await get_order_or_404(db, user_id, order_id, for_update=True)

    # 2. Only PENDING orders can be cancelled (no refund logic exists for PAID)
    if order.status != OrderStatus.PENDING:
        raise InvalidStatusTransitionError(order.status)

    # 3. Restore stock, locking products in a fixed order (sorted by product_id)
    for item in sorted(order.items, key=lambda i: i.product_id):
        product_result = await db.execute(
            select(Product).where(Product.id == item.product_id).with_for_update()
        )
        product = product_result.scalar_one_or_none()
        if product is None:
            raise ValueError(f"Product {item.product_id} missing for order {order.id}")
        product.stock_quantity += item.quantity

    # 4. One commit for the whole transaction
    order.status = OrderStatus.CANCELLED
    await db.commit()
    await db.refresh(order, attribute_names=["items"])
    return order