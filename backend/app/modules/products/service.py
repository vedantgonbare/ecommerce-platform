from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.products.models import Product
from app.modules.products.schemas import ProductCreate, ProductUpdate
from app.modules.categories.models import Category
import uuid
from sqlalchemy import select, func

class CategoryNotFoundError(Exception):
    pass

class ProductNotFoundError(Exception):
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


async def get_product_or_404(db: AsyncSession, product_id: uuid.UUID) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise ProductNotFoundError()
    return product

async def update_product(db, product_id, update_data: ProductUpdate):
    product = await get_product_or_404(db, product_id)  # reuse your existing fetch helper

    update_fields = update_data.model_dump(exclude_unset=True)

    if "category_id" in update_fields:
        category = await db.get(Category, update_fields["category_id"])
        if category is None:
            raise CategoryNotFoundError()  # reuse the same exception from create_product

    for field, value in update_fields.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product

async def delete_product(db, product_id):
    product = await get_product_or_404(db, product_id)
    await db.delete(product)
    await db.commit()


async def search_products(db: AsyncSession, query: str) -> list[Product]:
    ts_query = func.plainto_tsquery("english", query)
    ts_vector = func.to_tsvector("english", Product.name)

    result = await db.execute(
        select(Product)
        .where(ts_vector.op("@@")(ts_query))
        .order_by(func.ts_rank(ts_vector, ts_query).desc())
    )
    return result.scalars().all()