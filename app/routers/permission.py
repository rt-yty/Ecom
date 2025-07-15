from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from starlette import status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models.user import User
from .auth import get_current_user

router = APIRouter(prefix="/permission", tags=["permission"])

@router.patch("/")
async def supplier_permission(db: Annotated[AsyncSession, Depends(get_db)],
                              get_user: Annotated[dict, Depends(get_current_user)], user_id: int):
    if not get_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have admin permission"
        )

    user = await db.scalar(select(User).where(User.id==user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found"
        )

    if user.is_supplier:
        await db.execute(update(User).where(User.id==user_id).values(is_supplier=False, is_customer=True))
        await db.commit()
        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "user is no longer supplier"
        }
    else:
        await db.execute(update(User).where(User.id==user_id).values(is_supplier=True, is_customer=False))
        await db.commit()
        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "user is now supplier"
        }


@router.delete("/delete")
async def delete_user(db: Annotated[AsyncSession, Depends(get_db)],
                       get_user: Annotated[dict, Depends(get_current_user)], user_id: int):
    if not get_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don`t have admin permission"
        )

    user = await db.scalar(select(User).where(User.id==user_id))

    if not user or user.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="user not found"
        )

    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you can`t delete admin user"
        )

    if user.is_active:
        await db.execute(update(User).where(User.id==user_id).values(is_active=False))
        await db.commit()
        return {
            "status_code": status.HTTP_200_OK,
            "transaction": "user is deleted"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user is already deleted"
        )