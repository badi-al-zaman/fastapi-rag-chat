from uuid import UUID

from sqlmodel import SQLModel, Field
from dataclasses import dataclass


# Generic message
class Message(SQLModel):
    message: str


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    user_id: UUID


@dataclass
class EmailData:
    html_content: str
    subject: str
