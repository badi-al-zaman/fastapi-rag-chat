# schemas_models.py
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy.dialects.postgresql import JSON


class SessionBase(SQLModel):
    title: str = "default_session_title"


class SessionCreate(SessionBase):
    pass


class SessionPublic(SessionBase):
    session_id: UUID
    user_id: UUID
    created_at: datetime
    last_active_at: datetime
    messages: List["MessagePublic"] = []


class SessionsPublic(SQLModel):
    data: list[SessionPublic]


class Session(SessionBase, table=True):
    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.user_id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                 sa_column=Column(DateTime(timezone=True)))
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                     sa_column=Column(DateTime(timezone=True)))

    user: "User" = Relationship(back_populates="sessions")
    messages: list["Message"] = Relationship(back_populates="session", sa_relationship_kwargs={
        "order_by": "Message.created_at"
    })  # cascade_delete=True,


from enum import Enum


class Role(str, Enum):
    system = "system"
    developer = "developer"
    user = "user"
    assistant = "assistant"
    function = "function"
    tool = "tool"
    chatbot = "chatbot"
    model = "model"


class MessageData(SQLModel):
    role: Role
    blocks: list[dict]
    additional_kwargs: dict


class MessageBase(SQLModel):
    data: dict = Field(sa_column=Column(JSON))
    tokens: Optional[int] = None


class MessageCreate(SQLModel):
    content: str
    session_id: UUID


class MessagePublic(MessageBase):
    message_id: UUID
    session_id: UUID
    created_at: datetime


class Message(MessageBase, table=True):
    message_id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_id: UUID = Field(foreign_key="session.session_id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),
                                 sa_column=Column(DateTime(timezone=True)))

    session: Session = Relationship(back_populates="messages")
    # retrieved_docs: list["MessageRetrievedDoc"] = Relationship(back_populates="message", ) # cascade_delete=True

# class RetrievedDoc(SQLModel, table=True):
#     retrieved_doc_id: UUID = Field(default_factory=uuid4, primary_key=True)
#     source_doc_id: str = None
#     title: Optional[str] = None
#     snippet: Optional[str] = None
#     score: float = None
#     meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))
#     created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), sa_column=Column(DateTime(timezone=True)))
#
#     __table_args__ = (
#         # Prevent duplicate snippets from same source
#         UniqueConstraint("source_doc_id", "snippet", name="uq_source_snippet"),
#     )
#
#     linked_messages: list["MessageRetrievedDoc"] = Relationship(back_populates="retrieved_doc", ) # cascade_delete=True
#
#
# class MessageRetrievedDoc(SQLModel, table=True):
#     id: UUID = Field(default_factory=uuid4, primary_key=True)
#     message_id: UUID = Field(foreign_key="message.message_id", ondelete="CASCADE")
#     retrieved_doc_id: UUID = Field(foreign_key="retrieveddoc.retrieved_doc_id", ondelete="CASCADE")
#     rank: Optional[int] = None
#
#     message: Message = Relationship(back_populates="retrieved_docs")
#     retrieved_doc: RetrievedDoc = Relationship(back_populates="linked_messages")
