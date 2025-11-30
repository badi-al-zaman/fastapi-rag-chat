from fastapi import FastAPI

from app.core.db import init_db, engine
from app.core.config import settings as server_settings
from app.utils.logger import logger

from app.controllers.conversation_controller import session_router
from app.controllers.rag_controller_v1 import router as rag_router_v1
from app.controllers.auth_controller import router as auth_router
from app.controllers.users_controller import router as users_router

from starlette.middleware.cors import CORSMiddleware

app = FastAPI(title=server_settings.PROJECT_NAME, description="Chat with multiple wiki articles :articles:")

# Set all CORS enabled origins
if server_settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=server_settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(session_router, tags=["Sessions | Conversations"])
app.include_router(rag_router_v1, prefix="/v1", tags=["Rag V1: Index, Search, Ask, Chat"])

from app.services.user_crud import create_user
from app.models.user_models import User, UserCreate
from app.core.security import get_password_hash
from sqlmodel import Session, select

# from app.core.db import get_db_session
# from typing import Annotated
#
# SessionDep = Annotated[Session, Depends(get_db_session)]
FIRST_SUPERUSER = server_settings.FIRST_SUPERUSER
FIRST_SUPERUSER_PASSWORD = server_settings.FIRST_SUPERUSER_PASSWORD


@app.on_event("startup")
def on_startup() -> None:
    logger.info("Starting up app...")

    # create all DB model in the first startup of the system
    init_db()

    # Create First superuser based on the server settings
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.email == FIRST_SUPERUSER)
        ).first()
        if not user:
            user_in = UserCreate(
                first_name="badi",
                last_name="al-zaman",
                username="brain",
                email=FIRST_SUPERUSER,
                password=FIRST_SUPERUSER_PASSWORD,
            )
            hashed_password = get_password_hash(user_in.password)
            _ = create_user(db=session, user=user_in, hashed_password=hashed_password, is_superuser=True)
    logger.info("Startup complete.")


@app.get("/")
async def root():
    return {"response": "Server is running. Get /docs to see the endpoints."}
