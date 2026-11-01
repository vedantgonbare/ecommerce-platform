import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.db.session import async_session_factory, engine
from app.modules.categories.models import Category
from app.modules.categories.schemas import CategoryCreate
from app.modules.categories.service import create_category
from app.modules.products.models import Product
from app.modules.products.schemas import ProductCreate
from app.modules.products.service import create_product

# category -> [(product name, price, stock, image_url or None)]
CATALOG = {
    "Electronics": [
        ("Bluetooth Speaker", "34.99", 40, None),
        ("USB-C Fast Charger", "14.99", 80, None),
        ("Wireless Headphones", "59.99", 25, None),
    ],
    "Home Appliances": [
        ("Electric Kettle", "29.99", 35, None),
        ("Air Fryer", "79.99", 20, None),
        ("Handheld Vacuum", "44.99", 30, None),
    ],
    "Sports & Fitness": [
        ("Yoga Mat", "19.99", 60, None),
        ("Adjustable Dumbbells", "89.99", 15, None),
        ("Steel Water Bottle", "12.99", 100, None),
    ],
    "Fashion": [
        ("Cotton T-shirt", "18.99", 70, None),
        ("Denim Jacket", "49.99", 25, None),
        ("Canvas Sneakers", "39.99", 45, None),
    ],
}


async def get_or_create_category(db, name: str) -> Category:
    result = await db.execute(select(Category).where(Category.name == name))
    category = result.scalars().first()
    if category is None:
        category = await create_category(db, CategoryCreate(name=name))
    return category


async def seed() -> None:
    if engine.url.database != "ecommerce_db":
        raise SystemExit(f"Refusing to seed database '{engine.url.database}'")
    print(f"Seeding database: {engine.url.database}")

    try:
        async with async_session_factory() as db:
            for category_name, products in CATALOG.items():
                category = await get_or_create_category(db, category_name)
                for name, price, stock, image_url in products:
                    result = await db.execute(select(Product).where(Product.name == name))
                    if result.scalars().first() is not None:
                        print(f"skip   {name}")
                        continue
                    await create_product(db, ProductCreate(
                        name=name,
                        price=Decimal(price),
                        stock_quantity=stock,
                        category_id=category.id,
                        image_url=image_url,
                    ))
                    print(f"added  {name}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())