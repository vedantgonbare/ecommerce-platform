import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.reviews.schemas import ReviewCreate, ReviewUpdate, ReviewResponse
from app.modules.reviews.service import (
    create_review,
    list_reviews_for_product,
    update_review,
    delete_review,
    ReviewNotFoundError,
    UnverifiedPurchaseError,
)

router = APIRouter(tags=["reviews"])


@router.post("/products/{product_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_product_review(
    product_id: uuid.UUID,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        review = await create_review(db, current_user.id, product_id, data)
    except UnverifiedPurchaseError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review products you have purchased",
        )
    return review


@router.get("/products/{product_id}/reviews", response_model=list[ReviewResponse])
async def get_product_reviews(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await list_reviews_for_product(db, product_id)


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
async def update_product_review(
    review_id: uuid.UUID,
    data: ReviewUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        review = await update_review(db, current_user.id, review_id, data)
    except ReviewNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await delete_review(db, current_user.id, review_id)
    except ReviewNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")