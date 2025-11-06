from fastapi import APIRouter, HTTPException
from openai import BaseModel
from starlette import status

from app.services.embedding_service import load_and_chunk_documents_v2
from app.services.embedding_service import setup_vector_database_v2
from app.services.retriever_service import search_query_pipline_v2
from app.services.generator_service import ask_agent_v2
from app.services.rag_service import run_complete_rag_pipeline_v2
from app.core.config import settings as server_settings
from app.utils.logger import logger

router = APIRouter()


class SearchResult(BaseModel):
    data: list


class AskResult(BaseModel):
    response: str


@router.post("/index")
def index_documents():
    try:
        # Step 1: Setup vector database client
        vector_store = setup_vector_database_v2()

        # Step 2: Load and chunk documents to the vector client
        load_and_chunk_documents_v2(vector_store, server_settings.DATA_DIR)
        return {"message": "documents Indexed successfully"}
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post("/search", response_model=SearchResult)
def search(query: str):
    try:
        return {"data": search_query_pipline_v2(query)}
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable. Please try again later.",
        )


@router.post("/ask", response_model=AskResult)
def ask(query: str):
    try:
        response = run_complete_rag_pipeline_v2(query)
        return {"response": str(response)}
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable. Please try again later.",
        )


from llama_index.core.memory import Memory
from app.core.db import async_engine as pg_engine


# from llama_index.core.llms import ChatMessage
# from llama_index.core.memory import ChatMemoryBuffer  # deprecated
# from llama_index.storage.chat_store.postgres import PostgresChatStore
#
# chat_store = PostgresChatStore.from_uri(
#     uri=str(server_settings.SQLALCHEMY_ASYN_DATABASE_URI),
# )
# messages = chat_store.get_messages("conversation1")
# if len(messages) == 0:
#     messages = [
#         ChatMessage(role="user", content="When did Adam graduate from college?"),
#         ChatMessage(role="chatbot", content="1755."),
#     ]
#  Role should be 'system', 'developer', 'user', 'assistant', 'function', 'tool', 'chatbot' or 'model'
#     chat_store.set_messages("conversation1", messages=messages)

# session = crud.get_full_session(db, session_id)


@router.post("/chat/{session_id}", response_model=AskResult)
async def chat_with_agent(query: str, session_id: str):
    # chat_memory = ChatMemoryBuffer.from_defaults(
    #     token_limit=3000,
    #     chat_store=chat_store,
    #     chat_store_key=session_id,
    # )
    chat_memory = Memory.from_defaults(
        token_limit=3000,
        async_engine=pg_engine,
        session_id=session_id,
        table_name="memory_table",
    )
    try:
        # Send the chat history to Agent
        response = await ask_agent_v2(query, chat_memory)
        return {"response": str(response)}
    except HTTPException:
        # Re-raise HTTPException so FastAPI can handle it properly
        raise
    except Exception as e:
        # Using the async get/set methods for consistency with async engine
        messages_before_error = await chat_memory.aget_all()
        if messages_before_error and messages_before_error[-1].blocks[0].text == query:
            # Remove the last message from the list in Python memory
            messages_before_error.pop()
            # Overwrite the DB history with the truncated list
            await chat_memory.aset(messages_before_error)

        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service temporarily unavailable. Please try again later.",
        )
