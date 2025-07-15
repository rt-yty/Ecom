from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import insert, select, update
from slugify import slugify

from app.backend.db_depends import get_db
from app.routers.auth import get_current_user
from app.schemas import CreateProduct
from app.models.products import Product
from app.models.category import Category

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/")
async def get_all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    all_products = await db.scalars(select(Product).join(Category).where(Category.is_active==True,
                                                               Product.is_active==True,
                                                               Product.stock > 0))

    if not all_products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="products not found"
        )

    return all_products.all()

@router.post("/")
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], create_product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_customer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have permission to create product"
        )

    category = await db.scalar(select(Category).where(Category.id==create_product.category))

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="category not found"
        )

    await db.execute(insert(Product).values(name=create_product.name,
                                            slug=slugify(create_product.name),
                                            description=create_product.description,
                                            price=create_product.price,
                                            image_url=create_product.image_url,
                                            stock=create_product.stock,
                                            supplier_id=get_user.get("id"),
                                            category_id=create_product.category,
                                            rating=0.0))

    await db.commit()

    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "successful"
    }


@router.get("/{category_slug}")
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug==category_slug))

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="category not found"
        )

    subcategories = await db.scalars(select(Category).where(Category.parent_id==category.id))
    categories_and_subcategories = [category.id] + [i.id for i in subcategories.all()]
    products_category = await db.scalars(select(Product).where(Product.category_id.in_(categories_and_subcategories),
                                                         Product.is_active==True,
                                                         Product.stock > 0))
    return products_category.all()

@router.get("/details/{product_slug}")
async def product_details(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug==product_slug))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found"
        )

    return product

@router.put("/{product_slug}")
async def update_product(db: Annotated[AsyncSession, Depends(get_db)],
                         product_slug: str, update_product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    product = await db.scalar(select(Product).where(Product.slug==product_slug))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found"
        )

    if get_user.get("is_customer") or get_user.get("id") != product.supplier_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have permission to update product"
        )

    category = await db.scalar(select(Category).where(Category.id==update_product.category))

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="category not found"
        )

    product.name = update_product.name
    product.description = update_product.description
    product.slug = slugify(update_product.name)
    product.price = update_product.price
    product.stock = update_product.stock
    product.image_url = update_product.image_url
    product.category_id = update_product.category

    await db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "product update is successful"
    }


@router.delete("/{product_slug}")
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)] ,product_slug: str,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found"
        )

    if get_user.get("is_customer") or get_user.get("id") != product.supplier_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have permission to update product"
        )

    product.is_active = False

    await db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "product delete is successful"
    }
