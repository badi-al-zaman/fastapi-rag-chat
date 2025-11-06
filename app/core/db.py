# database.py
from fastapi import Depends
from typing import Annotated, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import create_engine, Session, select, SQLModel

from app.core.config import settings as server_settings

# from app.models.user_models import User, UserCreate
# from app.models.user_crud import create_user
import app.models.conversation_models
import app.models.document_models

SYN_DATABASE_URI = str(server_settings.SQLALCHEMY_SYN_DATABASE_URI)
ASYN_DATABASE_URI = str(server_settings.SQLALCHEMY_ASYN_DATABASE_URI)
FIRST_SUPERUSER = server_settings.FIRST_SUPERUSER
FIRST_SUPERUSER_PASSWORD = server_settings.FIRST_SUPERUSER_PASSWORD

# psycopg3 works directly with SQLModel's create_engine
engine = create_engine(SYN_DATABASE_URI)  # echo=False


# get DB session
def get_db_session():
    with Session(engine) as session:
        yield session


def init_db() -> None:
    # make sure all SQLModel models are imported (app.models) before initializing DB
    # otherwise, SQLModel might fail to initialize relationships properly
    SQLModel.metadata.create_all(engine)

    # with Session(engine) as session:
    #     user = session.exec(
    #         select(User).where(User.email == FIRST_SUPERUSER)
    #     ).first()
    #     if not user:
    #         user_in = UserCreate(
    #             email=FIRST_SUPERUSER,
    #             password=FIRST_SUPERUSER_PASSWORD,
    #         )
    #         user = create_user(db=session, user=user_in)
    #         print(user)


# Step 1: Create async engine and session
async_engine = create_async_engine(
    ASYN_DATABASE_URI,  # Async connection string
    # echo=True,  # Optional: Set to False in production
    future=True,
)

# Step 2: Set up async session
async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Step 3: Create a dependency to yield an async session
async def _get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


# Wrap _get_async_session with Depends on FastAPI to keep type checking happy
get_async_session = Depends(_get_async_session)

SessionDep = Annotated[Session, Depends(get_db_session)]
