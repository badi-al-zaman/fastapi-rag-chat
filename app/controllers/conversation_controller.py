from fastapi import APIRouter
from app.core.db import SessionDep
import app.models.conversation_crud as conversation_crud
import app.models.conversation_models as conversation_models
from uuid import UUID

session_router = APIRouter()


@session_router.post("/sessions", response_model=conversation_models.SessionPublic)
def create_chat_session(payload: conversation_models.SessionCreate, db: SessionDep):
    return conversation_crud.create_session(db, **payload.model_dump())


@session_router.get("/sessions/{session_id}", response_model=conversation_models.SessionPublic)
def get_full_session(session_id: str, db: SessionDep):
    return conversation_crud.get_full_session(db, session_id)


@session_router.delete("/sessions/{session_id}")
def delete_session(session_id: UUID, db: SessionDep):
    return conversation_crud.delete_session(db, session_id)


@session_router.get("/sessions", response_model=conversation_models.SessionsPublic)
def get_all_sessions(db: SessionDep, limit: int = 10):
    return {"data": conversation_crud.get_all_sessions(db, limit)}

# from app.models.conversation_models import MessageData
# @session_router.post("/sessions/{session_id}/messages")
# def add_message(msg: conversation_models.MessageCreate, db: SessionDep):
#     md = MessageData(
#         role="user",
#         additional_kwargs={},
#         blocks=[{"block_type": "text", "text": msg.content}],
#     )
#     new_message = conversation_crud.add_message(db, msg.session_id, data=md.model_dump())
#     db.commit()
#     db.refresh(new_message)
#     return new_message

# @session_router.post("/messages/{message_id}/retrieved_docs")
# def attach_docs(message_id: str, docs: List[dict], db: SessionDep):
#     conversation_crud.attach_retrieved_docs(db, message_id, docs)
#     return {"status": "ok"}
