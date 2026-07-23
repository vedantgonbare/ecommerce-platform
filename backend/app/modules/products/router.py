from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.modules.products.schemas import ProductCreate, ProductResponse, ProductUpdate
from app.modules.products.service import (
    create_product,
    CategoryNotFoundError,
    get_all_products,
    get_product_or_404,
    ProductNotFoundError,
    update_product,
    delete_product,
)
import uuid

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create(product_data: ProductCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_product = await create_product(db, product_data)
    except CategoryNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category does not exist")
    return new_product

@router.get("/", response_model=list[ProductResponse])
async def list_products(db: AsyncSession = Depends(get_db)):
    return await get_all_products(db)

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        product = await get_product_or_404(db, product_id)
    except ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductResponse)
async def update(product_id: uuid.UUID, update_data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    try:
        updated_product = await update_product(db, product_id, update_data)
    except ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    except CategoryNotFoundError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category does not exist")
    return updated_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        await delete_product(db, product_id)
    except ProductNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")