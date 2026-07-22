from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.modules.categories.schemas import CategoryCreate, CategoryResponse
from app.modules.categories.service import create_category, SlugAlreadyExistsError
import uuid
from app.modules.categories.service import get_all_categories, get_category_by_id
from app.modules.categories.schemas import CategoryUpdate
from app.modules.categories.service import update_category
from app.modules.categories.service import delete_category, CategoryHasChildrenError

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create(category_data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_category = await create_category(db, category_data)
    except SlugAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with this name already exists")
    return new_category

@router.get("/", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    return await get_all_categories(db)

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    category = await get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=CategoryResponse)
async def update(category_id: uuid.UUID, update_data: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    category = await get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    try:
        updated_category = await update_category(db, category, update_data)
    except SlugAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A category with this name already exists")
    return updated_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    category = await get_category_by_id(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    try:
        await delete_category(db, category)
    except CategoryHasChildrenError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot delete a category that has subcategories")