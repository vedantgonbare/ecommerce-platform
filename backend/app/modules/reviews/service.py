import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.orders.models import Order, OrderItem, OrderStatus
from app.modules.reviews.models import Review
from app.modules.reviews.schemas import ReviewCreate, ReviewUpdate


class ReviewNotFoundError(Exception):
    pass


class UnverifiedPurchaseError(Exception):
    pass


async def has_verified_purchase(db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID) -> bool:
    result = await db.execute(
        select(Order.id)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .where(
            Order.user_id == user_id,
            OrderItem.product_id == product_id,
            Order.status.in_([OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED]),
        )
    )
    return result.first() is not None


async def create_review(
    db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID, data: ReviewCreate
) -> Review:
    if not await has_verified_purchase(db, user_id, product_id):
        raise UnverifiedPurchaseError()

    review = Review(
        product_id=product_id,
        user_id=user_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


async def list_reviews_for_product(db: AsyncSession, product_id: uuid.UUID) -> list[Review]:
    result = await db.execute(
        select(Review).where(Review.product_id == product_id).order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())

async def get_review_or_404(db: AsyncSession, user_id: uuid.UUID, review_id: uuid.UUID) -> Review:
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.user_id == user_id)
    )
    review = result.scalar_one_or_none()

    if review is None:
        raise ReviewNotFoundError(review_id)

    return review


async def update_review(
    db: AsyncSession, user_id: uuid.UUID, review_id: uuid.UUID, data: ReviewUpdate
) -> Review:
    review = await get_review_or_404(db, user_id, review_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)
    return review


async def delete_review(db: AsyncSession, user_id: uuid.UUID, review_id: uuid.UUID) -> None:
    review = await get_review_or_404(db, user_id, review_id)
    await db.delete(review)
    await db.commit()