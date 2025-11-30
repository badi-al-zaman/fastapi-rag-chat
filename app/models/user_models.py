# schemas_models.py
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr


class UserBase(SQLModel):
    username: str | None = Field(default=None, max_length=255, unique=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    first_name: str = Field(min_length=3, max_length=255)
    last_name: str = Field(min_length=3, max_length=255)
    is_active: bool = True


# Properties to receive when create user
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    username: str | None = Field(default=None, max_length=255, unique=True)
    first_name: str = Field(min_length=3, max_length=255)
    last_name: str = Field(min_length=3, max_length=255)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    first_name: str = Field(min_length=3, max_length=255)
    last_name: str = Field(min_length=3, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    user_id: UUID


class User(UserBase, table=True):
    user_id: UUID = Field(default_factory=uuid4, primary_key=True)
    is_superuser: bool = False
    hashed_password: str  # need to be hashed before store it into DB
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    sessions: list["Session"] = Relationship(
        back_populates="user",
        passive_deletes=True)  # cascade_delete=True -> here mean When I delete a user through the ORM, also issue DELETE statements for the child objects.


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
