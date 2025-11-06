# models.py
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Properties to receive when create user
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    user_id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str  # need to be hashed before store it into DB

    sessions: list["Session"] = Relationship(back_populates="user", cascade_delete=True)
