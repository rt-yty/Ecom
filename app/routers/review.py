from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from sqlalchemy import insert, select, update

from app.backend.db_depends import get_db
from app.models.review import Review
from app.routers.auth import get_current_user
from app.schemas import CreateReview
from app.models.products import Product

router = APIRouter(prefix="/review", tags=["review"])

@router.get("/")
async def get_all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await db.scalars(select(Review).join(Product).where(Product.is_active==True,
                                                                  Review.is_active==True))

    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no reviews found"
        )

    return reviews.all()


@router.get("/{user_id}")
async def get_reviews_by_user(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
    reviews = await db.scalars(select(Review).where(Review.is_active==True,
                                                    Review.user_id==user_id))
    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no reviews found"
        )

    return reviews.all()

@router.post("/")
async def add_review(db: Annotated[AsyncSession, Depends(get_db)],
                             create_review: CreateReview, get_user: Annotated[dict, Depends(get_current_user)]):
    review = await db.scalar(select(Review).where(Review.product_id==create_review.product_id,
                                                  Review.user_id==get_user.get("id"),
                                                  Review.is_active==True))
    if review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="you already reviewed this product"
        )

    product = await db.scalar(select(Product).where(Product.id==create_review.product_id))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found"
        )

    await db.execute(insert(Review).values(product_id=create_review.product_id,
                                           user_id=get_user.get("id"),
                                           comment=create_review.comment,
                                           grade=create_review.grade))

    await db.execute(update(Product).where(Product.id==create_review.product_id).values(counter_reviews=Product.counter_reviews+1,
                                                                                        rating=((Product.rating*Product.counter_reviews)+create_review.grade)/(Product.counter_reviews+1)))

    await db.commit()

    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "successful"
    }


@router.get("/{product_slug}")
async def get_reviews_by_slug(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug==product_slug))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="product not found"
        )

    reviews = await db.scalars(select(Review).where(Review.product_id==product.id,
                                                    Review.is_active==True))
    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no reviews found"
        )

    return reviews.all()


@router.put("/{review_id}")
async def update_review(db: Annotated[AsyncSession, Depends(get_db)], review_id: int,
                        get_user: Annotated[dict, Depends(get_current_user)],
                        update_review: CreateReview):
    review = await db.scalar(select(Review).where(Review.id==review_id,
                                                  Review.is_active==True))
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="review not found"
        )

    if not get_user.get("is_admin") and not get_user.get("id")==review.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have permission"
        )

    await db.execute(update(Review).where(Review.id==review_id).values(grade=update_review.grade,
                                                                       comment=update_review.comment))
    await db.execute(update(Product).where(Product.id==review.product_id).values(rating=((Product.rating*Product.counter_reviews) - review.grade) / (Product.counter_reviews - 1)))

    await db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "review update is successful"
    }


@router.delete("/{review_id}")
async def delete_review(db: Annotated[AsyncSession, Depends(get_db)], review_id: int,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    review = await db.scalar(select(Review).where(Review.id==review_id))
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="review not found"
        )

    if not get_user.get("is_admin") and not get_user.get("id")==review.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have permission"
        )

    if not review.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="review already deleted"
        )

    await db.execute(update(Review).where(Review.id==review_id).values(is_active=False))
    await db.execute(update(Product).where(Product.id==review.product_id).values(counter_reviews=Product.counter_reviews-1,
                                                                                 rating=((Product.rating*Product.counter_reviews)-(review.grade))/(Product.counter_reviews-1)))
    await db.commit()

    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "review delete is successful"
    }