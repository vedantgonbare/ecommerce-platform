import uuid
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.orders.service import OrderNotFoundError, InvalidStatusTransitionError
from app.modules.payments.schemas import CheckoutSessionResponse
from app.modules.payments.service import create_checkout_session, mark_order_paid

router = APIRouter(prefix="/orders", tags=["payments"])


@router.post("/{order_id}/checkout", response_model=CheckoutSessionResponse)
async def checkout_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        checkout_url, session_id = await create_checkout_session(
            db, current_user.id, order_id
        )
    except OrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return CheckoutSessionResponse(checkout_url=checkout_url, session_id=session_id)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session["metadata"]["order_id"]
        await mark_order_paid(db, order_id)

    return {"status": "success"}