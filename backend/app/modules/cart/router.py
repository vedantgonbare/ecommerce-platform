from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.cart.schemas import CartResponse, CartItemAdd, CartItemUpdate
from app.modules.cart.service import (
    get_cart,
    add_item_to_cart,
    update_item_quantity,
    remove_item_from_cart,
    CartItemNotFoundError,
)
from app.modules.products.service import ProductNotFoundError

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartResponse)
async def view_cart(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_cart(db, current_user.id)


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    item_data: CartItemAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await add_item_to_cart(db, current_user.id, item_data.product_id, item_data.quantity)
    except ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product does not exist")


@router.put("/items/{product_id}", response_model=CartResponse)
async def update_item(
    product_id: uuid.UUID,
    item_data: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await update_item_quantity(db, current_user.id, product_id, item_data.quantity)
    except CartItemNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart")


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_item(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await remove_item_from_cart(db, current_user.id, product_id)
    except CartItemNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found in cart")