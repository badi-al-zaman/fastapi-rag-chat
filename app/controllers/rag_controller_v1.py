from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette import status

from app.core.db import SessionDep
from app.models.conversation_models import MessageData
from app.services.embedding_service import load_and_chunk_documents
from app.services.embedding_service import setup_vector_database
from app.services.retriever_service import search_query_pipline
from app.services.generator_service import ask_agent_v1
from app.services.rag_service import run_complete_rag_pipeline
import app.services.conversation_crud as conversation_crud
from app.core.config import settings as server_settings

from app.utils.logger import logger

router = APIRouter()


class RetrievedDoc(BaseModel):
    id: str
    content: str
    metadata: dict
    similarity: float


class IndexSearchResults(BaseModel):
    data: List[RetrievedDoc]


class AskResponse(BaseModel):
    response: str


@router.post("/index")
def index_documents():
    try:
        # Step 1: Load and chunk documents
        chunks = load_and_chunk_documents(server_settings.DATA_DIR)

        # Step 2: Setup vector database client and add chunks to embed them
        _ = setup_vector_database(chunks)
        return {"response": "documents Indexed successfully"}
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post("/search", response_model=IndexSearchResults)
def search(query: str):
    try:
        return {"data": search_query_pipline(query)}
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post("/ask", response_model=AskResponse)
def ask(query: str):
    try:
        response = run_complete_rag_pipeline(query)
        return {"response": str(response)}
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post("/chat/{session_id}", response_model=AskResponse)
async def chat_with_agent(query: str, session_id: str, db: SessionDep):
    try:
        u_md = MessageData(
            role="user",
            additional_kwargs={},
            blocks=[{"block_type": "text", "text": query}],
        )
        # Store user message in DB
        _ = conversation_crud.add_message(db, session_id,
                                          data=u_md.model_dump(),
                                          tokens=None)

        # Get the chat history after we store the new user message
        session = conversation_crud.get_full_session(db, session_id)

        # Send the chat history to Agent
        response = await ask_agent_v1(session, db)

        # Store agent response
        conversation_crud.add_message(db, session_id, data=response.message.model_dump(), tokens=None)

        # Commit the transaction if the response succeeded
        db.commit()  # db.refresh(new_message)

        return {"response": str(response)}
    except HTTPException:
        # rollback the transaction if any errors happened
        db.rollback()
        # Re-raise HTTPException so FastAPI can handle it properly
        raise
    except Exception as e:
        # rollback the transaction if any errors happened
        db.rollback()
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable. Please try again later.",
        )
