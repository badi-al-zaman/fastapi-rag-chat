# crud.py
from typing import Any

from sqlalchemy import delete, func
from sqlmodel import Session, select, col

from app.core.security import verify_password, get_password_hash
from app.models.schemas_models import Message
from app.models.user_models import User, UserRegister, UserUpdate, UsersPublic
from app.models.conversation_models import Session as Conversation
from pydantic import EmailStr


def create_user(db: Session, user: UserRegister, hashed_password: str, is_superuser: bool = False) -> User:
    new_user = User(**user.model_dump(), hashed_password=hashed_password, is_superuser=is_superuser)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user(*, db: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(*, db: Session, user: User) -> Message:
    db.delete(user)
    db.commit()
    return Message(message="User deleted successfully")


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# def get_user(db: Session, username: str):
#     db_user = db.query(User).filter(User.username == username).first()
#     return db_user


def get_user(db: Session, username: str = None, email: EmailStr = None) -> User | None:
    statement = select(User).where((User.username == username) | (User.email == email))
    session_user = db.exec(statement).first()
    return session_user


def get_user_by_username(db: Session, username: str) -> User | None:
    statement = select(User).where(User.username == username)
    session_user = db.exec(statement).first()
    return session_user


def get_user_by_email(db: Session, email: EmailStr) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = db.exec(statement).first()
    return session_user


def get_all_users(db: Session, skip: int, limit: int) -> Any:
    count_statement = select(func.count()).select_from(User)
    count = db.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = db.exec(statement).all()

    return UsersPublic(data=users, count=count)
