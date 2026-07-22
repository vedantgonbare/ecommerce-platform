from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.products.models import Product
from app.modules.products.schemas import ProductCreate
from app.modules.categories.models import Category
import uuid

class CategoryNotFoundError(Exception):
    pass

async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
    result = await db.execute(select(Category).where(Category.id == product_data.category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise CategoryNotFoundError()

    new_product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock_quantity=product_data.stock_quantity,
        category_id=product_data.category_id,
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


async def get_all_products(db: AsyncSession) -> list[Product]:
    result = await db.execute(select(Product))
    return result.scalars().all()


async def get_product_by_id(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()