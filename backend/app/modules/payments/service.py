import stripe
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.orders.service import get_order_or_404, InvalidStatusTransitionError, OrderNotFoundError
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.modules.orders.models import Order, OrderStatus
from app.modules.payments.tasks import send_payment_confirmation

async def create_checkout_session(
    db: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID
) -> tuple[str, str]:
    order = await get_order_or_404(db, user_id, order_id)

    if order.status != OrderStatus.PENDING:
        raise InvalidStatusTransitionError(order.status)

    line_items = [
        {
            "price_data": {
                "currency": "usd",
                "product_data": {"name": item.product_name},
                "unit_amount": int(item.unit_price * 100),
            },
            "quantity": item.quantity,
        }
        for item in order.items
    ]

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url="http://localhost:5173/orders/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:5173/orders/cancel",
        metadata={"order_id": str(order.id)},
    )

    order.stripe_checkout_session_id = session.id
    await db.commit()

    return session.url, session.id


async def mark_order_paid(db: AsyncSession, order_id: str) -> None:
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()

    if order is None:
        return  # unknown order_id — nothing to update, silently ignore

    order.status = OrderStatus.PAID
    await db.commit()

    send_payment_confirmation.delay(order_id)

async def get_order_by_session_id(db: AsyncSession, session_id: str) -> Order:
    result = await db.execute(
        select(Order)
        .where(Order.stripe_checkout_session_id == session_id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()

    if order is None:
        raise OrderNotFoundError(session_id)

    return order