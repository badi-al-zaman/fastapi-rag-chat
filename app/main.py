from fastapi import FastAPI
from app.core.config import settings as server_settings

from app.core.db import init_db
from app.utils.logger import logger
from app.controllers.conversation_controller import session_router

app = FastAPI(title=server_settings.PROJECT_NAME, description="Chat with multiple wiki articles :articles:")
app.include_router(session_router, tags=["Sessions | Conversations"])


@app.on_event("startup")
def on_startup():
    logger.info("Starting up app...")
    init_db()
    logger.info("Startup complete.")


@app.get("/")
async def root():
    return {"response": "Server is running. Get /docs to see the endpoints."}
