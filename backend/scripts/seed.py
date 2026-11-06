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
        ("Bluetooth Speaker", "34.99", 40, "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
        ("USB-C Fast Charger", "14.99", 80, "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
        ("Wireless Headphones", "59.99", 25, "https://plus.unsplash.com/premium_photo-1679513691485-711d030f7e94?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
    ],
    "Home Appliances": [
        ("Electric Kettle", "29.99", 35, "https://images.unsplash.com/photo-1738520420652-0c47cea3922b?w=600&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
        ("Air Fryer", "79.99", 20, "https://plus.unsplash.com/premium_photo-1711051351678-658b273f71d4?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
        ("Handheld Vacuum", "44.99", 30, "https://images.unsplash.com/photo-1765970101531-8d116223af49?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
    ],
    "Sports & Fitness": [
        ("Yoga Mat", "19.99", 60, "https://images.unsplash.com/photo-1767605545968-a102fc151b08?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
        ("Adjustable Dumbbells", "89.99", 15, "https://images.unsplash.com/photo-1703668984128-b506579acdd2?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
        ("Steel Water Bottle", "12.99", 100, "https://images.unsplash.com/photo-1568395216634-ab1b1e848751?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
    ],
    "Fashion": [
        ("Cotton T-shirt", "18.99", 70, "https://plus.unsplash.com/premium_photo-1718913931807-4da5b5dd27fa?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
        ("Denim Jacket", "49.99", 25, "https://images.unsplash.com/photo-1772985451338-6bbc32aeedf1?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
        ("Canvas Sneakers", "39.99", 45, "https://images.unsplash.com/photo-1771049873881-45b23a2e9847?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=NHwxMjA3fDA%3D"),
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