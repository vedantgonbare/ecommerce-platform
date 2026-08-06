import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cart.models import Cart, CartItem
from app.modules.cart.schemas import CartItemResponse, CartResponse
from app.modules.products.models import Product
from app.modules.products.service import ProductNotFoundError

class CartItemNotFoundError(Exception):
    pass


async def get_or_create_cart(db: AsyncSession, user_id: uuid.UUID) -> Cart:
    result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    cart = result.scalar_one_or_none()

    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    return cart


async def _build_cart_response(db: AsyncSession, cart: Cart) -> CartResponse:
    result = await db.execute(
        select(CartItem, Product)
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.cart_id == cart.id)
    )
    rows = result.all()

    items = [
        CartItemResponse(
            id=cart_item.id,
            product_id=cart_item.product_id,
            product_name=product.name,
            product_price=product.price,
            quantity=cart_item.quantity,
        )
        for cart_item, product in rows
    ]

    subtotal = sum((item.product_price * item.quantity for item in items), Decimal("0"))

    return CartResponse(id=cart.id, user_id=cart.user_id, items=items, subtotal=subtotal)


async def get_cart(db: AsyncSession, user_id: uuid.UUID) -> CartResponse:
    cart = await get_or_create_cart(db, user_id)
    return await _build_cart_response(db, cart)


async def add_item_to_cart(
    db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int
) -> CartResponse:
    product_result = await db.execute(select(Product).where(Product.id == product_id))
    if product_result.scalar_one_or_none() is None:
        raise ProductNotFoundError()

    cart = await get_or_create_cart(db, user_id)

    existing_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    existing_item = existing_result.scalar_one_or_none()

    if existing_item is not None:
        existing_item.quantity += quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity))

    await db.commit()
    return await _build_cart_response(db, cart)

async def update_item_quantity(
    db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int
) -> CartResponse:
    cart = await get_or_create_cart(db, user_id)

    result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    item = result.scalar_one_or_none()

    if item is None:
        raise CartItemNotFoundError()

    item.quantity = quantity
    await db.commit()
    return await _build_cart_response(db, cart)


async def remove_item_from_cart(
    db: AsyncSession, user_id: uuid.UUID, product_id: uuid.UUID
) -> CartResponse:
    cart = await get_or_create_cart(db, user_id)

    result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    item = result.scalar_one_or_none()

    if item is None:
        raise CartItemNotFoundError()

    await db.delete(item)
    await db.commit()
    return await _build_cart_response(db, cart)