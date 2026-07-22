import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.categories.models import Category
from sqlalchemy.exc import IntegrityError
from app.modules.categories.schemas import CategoryCreate
from sqlalchemy import select
import uuid
from app.modules.categories.schemas import CategoryCreate, CategoryUpdate

def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)   # strip non-alphanumeric (except spaces/hyphens)
    slug = re.sub(r"[\s_]+", "-", slug)     # collapse spaces/underscores into hyphens
    slug = re.sub(r"-+", "-", slug).strip("-")  # collapse repeat hyphens, trim edges
    return slug

class SlugAlreadyExistsError(Exception):
    pass

async def create_category(db: AsyncSession, category_data: CategoryCreate) -> Category:
    slug = slugify(category_data.name)

    new_category = Category(
        name=category_data.name,
        slug=slug,
        parent_id=category_data.parent_id,
    )
    db.add(new_category)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise SlugAlreadyExistsError()

    await db.refresh(new_category)
    return new_category


async def get_all_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category))
    return result.scalars().all()

async def get_category_by_id(db: AsyncSession, category_id: uuid.UUID) -> Category | None:
    result = await db.execute(select(Category).where(Category.id == category_id))
    return result.scalar_one_or_none()

async def update_category(db: AsyncSession, category: Category, update_data: CategoryUpdate) -> Category:
    if update_data.name is not None:
        category.name = update_data.name
        category.slug = slugify(update_data.name)
    if update_data.parent_id is not None:
        category.parent_id = update_data.parent_id

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise SlugAlreadyExistsError()

    await db.refresh(category)
    return category

class CategoryHasChildrenError(Exception):
    pass

async def delete_category(db: AsyncSession, category: Category) -> None:
    result = await db.execute(select(Category).where(Category.parent_id == category.id))
    if result.scalar_one_or_none() is not None:
        raise CategoryHasChildrenError()

    await db.delete(category)
    await db.commit()