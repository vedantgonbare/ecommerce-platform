import stripe
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import OrderStatus
from app.modules.orders.service import get_order_or_404, InvalidStatusTransitionError


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
        success_url="http://localhost:8000/payments/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:8000/payments/cancel",
        metadata={"order_id": str(order.id)},
    )

    order.stripe_checkout_session_id = session.id
    await db.commit()

    return session.url, session.id