from fastapi import FastAPI
from app.core.config import settings as server_settings

from app.core.db import init_db
from app.utils.logger import logger
from app.controllers.conversation_controller import session_router
from app.controllers.rag_controller_v2 import router as rag_router_v2

app = FastAPI(title=server_settings.PROJECT_NAME, description="Chat with multiple wiki articles :articles:")
app.include_router(session_router, tags=["Sessions | Conversations"])
app.include_router(rag_router_v2, prefix="/v2", tags=["Rag V2: Index, Search, Ask, Chat"])


@app.on_event("startup")
def on_startup():
    logger.info("Starting up app...")
    init_db()
    logger.info("Startup complete.")


@app.get("/")
async def root():
    return {"response": "Server is running. Get /docs to see the endpoints."}
