from uuid import UUID
from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from app.core.db import SessionDep
from app.core.security import get_current_active_superuser, CurrentUser, verify_password, \
    get_password_hash
from app.models.schemas_models import Message, UpdatePassword
import app.services.user_crud as crud
from app.models.user_models import UsersPublic, User, UserPublic, UserUpdateMe, UserRegister, \
    UserUpdate

router = APIRouter()


@router.post("/register", response_model=UserPublic)
def register_user(user: UserRegister, db: SessionDep):
    """Register a new user."""
    db_user = crud.get_user(db, user.username, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="The user with this email | username already exists in the system.")
    hashed_password = get_password_hash(user.password)
    return crud.create_user(db, user, hashed_password=hashed_password)


@router.get("/users/me/", response_model=UserPublic)
async def read_users_me(current_user: CurrentUser):
    """Get current user info"""
    return current_user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
        *, db: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """
    if user_in.email:
        existing_user = crud.get_user_by_email(db=db, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
        *, db: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    db.add(current_user)
    db.commit()
    return Message(message="Password updated successfully")


@router.delete("/me", response_model=Message)
def delete_user_me(db: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    return crud.delete_user(db=db, user=current_user)


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(db: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    return crud.get_all_users(db, skip, limit)


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
        user_id: UUID, db: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
        *,
        db: SessionDep,
        user_id: UUID,
        user_in: UserUpdate,
) -> Any:
    """
    Update a user.
    """

    db_user = db.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(db=db, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    return crud.update_user(db=db, db_user=db_user, user_in=user_in)


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
        db: SessionDep, current_user: CurrentUser, user_id: UUID
) -> Message:
    """
    Delete a user.
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    return crud.delete_user(db=db, user=user)
