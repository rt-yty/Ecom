from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import insert, select, update
from slugify import slugify

from app.backend.db_depends import get_db
from app.routers.auth import get_current_user
from app.schemas import CreateCategory
from app.models.category import Category


router = APIRouter(prefix="/category", tags=["category"])

@router.get("/")
async def get_all_categories(db: Annotated[AsyncSession, Depends(get_db)]):
    categories = await db.scalars(select(Category).where(Category.is_active==True))
    return categories.all()

@router.post("/",  status_code=status.HTTP_201_CREATED)
async def create_category(db: Annotated[AsyncSession, Depends(get_db)], create_category: CreateCategory,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have admin permission"
        )

    await db.execute(insert(Category).values(name=create_category.name,
                                       parent_id=create_category.parent_id,
                                       slug=slugify(create_category.name)))

    await db.commit()

    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "successful"
    }

@router.put("/{category_slug}")
async def update_category(db: Annotated[AsyncSession, Depends(get_db)],
                          category_slug: str, update_category: CreateCategory,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have admin permission"
        )

    category = await db.scalar(select(Category).where(Category.slug==category_slug))

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="category not found"
        )

    category.name = update_category.name
    category.parent_id = update_category.parent_id
    category.slug = slugify(update_category.name)

    await db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "category update is successful"
    }


@router.delete("/{category_slug}")
async def delete_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if not get_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have admin permission"
        )

    category = await db.scalar(select(Category).where(Category.slug==category_slug,
                                                      Category.is_active==True))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="category not found"
        )

    category.is_active = False

    await db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "category delete is successful"
    }

