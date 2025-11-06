# crud.py
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from app.models.conversation_models import Session as ChatSession, Message, MessageData

from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.utils.logger import logger


def create_session(db: Session, title: str = None, user_id=None, metadata=None):
    try:
        new_session = ChatSession(title=title)  # user_id=user_id
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        return new_session
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating new session."
        )
    except Exception as e:
        db.rollback()
        # Catch any other unexpected exceptions
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


def delete_session(db: Session, session_id: str):
    try:
        session = db.get(ChatSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session with id={session_id} not found."
            )
        db.delete(session)
        db.commit()
        return {"ok": True}
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle it properly
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deleting session."
        )
    except Exception as e:
        db.rollback()
        # Catch any other unexpected exceptions
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


def get_full_session(db: Session, session_id: str):
    try:
        query = (
            select(ChatSession)
            .where(ChatSession.session_id == session_id)
            .options(
                selectinload(ChatSession.messages)
            )
        )

        session_obj = db.exec(query).one_or_none()
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session with id={session_id} not found."
            )

        return session_obj
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle it properly
        raise
    except SQLAlchemyError as e:
        # Optionally log e for debugging
        logger.exception(f"Unexpected error: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while get session's messages."
        )
    except Exception as e:
        logger.error(str(e))
        # Catch any other unexpected exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


def get_all_sessions(db: Session, limit: int = 10):
    try:
        sessions = db.exec(select(ChatSession).order_by(ChatSession.created_at.desc()).limit(limit)).all()
        return sessions
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while get all sessions."
        )
    except Exception as e:
        # Catch any other unexpected exceptions
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


def add_message(db: Session, session_id, data: dict, tokens=None):
    try:
        # Get the chat session
        session = db.get(ChatSession, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session with id={session_id} not found."
            )

        # Create the message
        message = Message(session_id=session_id, data=data, tokens=tokens)
        db.add(message)

        # Update session last active
        session.last_active_at = datetime.now(timezone.utc)
        return message
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle it properly
        raise
    except SQLAlchemyError as e:
        logger.exception(f"Unexpected error: {str(e)}")
        # Optionally log e for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while adding message."
        )
    except Exception as e:
        logger.error(str(e))
        # Catch any other unexpected exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

# def get_messages(db: Session, session_id: str, limit: int = 50):
#     stmt = select(Message).where(Message.session_id == session_id).order_by(Message.created_at.desc()).limit(limit)
#     return db.exec(stmt).all()[::-1]  # return ascending order
# from app.models.conversation_models import RetrievedDoc, MessageRetrievedDoc
# from typing import List
# def attach_retrieved_docs(db: Session, message_id, docs: List[dict]):
#     """
#     docs: list of {source_doc_id, title, snippet, score, metadata, rank}
#     This will insert retrieved_docs and link them to the message.
#     """
#     try:
#         for d in docs:
#             existing = db.exec(
#                 select(RetrievedDoc).where(
#                     (RetrievedDoc.source_doc_id == d.get("id")) &
#                     (RetrievedDoc.snippet == d.get("content"))
#                 )
#             ).first()
#
#             if existing:
#                 link = MessageRetrievedDoc(message_id=message_id, retrieved_doc_id=existing.retrieved_doc_id,
#                                            rank=d.get("similarity"))
#                 db.add(link)
#                 continue
#             else:
#                 rd = RetrievedDoc(
#                     source_doc_id=d.get("id"),
#                     title=d.get("title"),
#                     snippet=d.get("content"),
#                     score=d.get("similarity"),
#                     meta=d.get("metadata")
#                 )
#
#                 db.add(rd)
#                 db.commit()
#                 db.refresh(rd)
#
#                 link = MessageRetrievedDoc(message_id=message_id, retrieved_doc_id=rd.retrieved_doc_id,
#                                            rank=d.get("similarity"))
#                 db.add(link)
#         db.commit()
#     except HTTPException:
#         # Re-raise HTTPException so FastAPI can handle it properly
#         db.rollback()
#         raise
#     except SQLAlchemyError as e:
#         db.rollback()
#         # Optionally log e for debugging
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Database error while adding retrieved_docs."
#         )
#     except Exception as e:
#         db.rollback()
#         # Catch any other unexpected exceptions
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Unexpected error: {str(e)}"
#         )
