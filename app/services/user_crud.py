# crud.py
from sqlmodel import Session, select
from app.models.user_models import User, UserCreate


def create_user(db: Session, user: UserCreate) -> User:
    new_user = User(**user.model_dump(), hashed_password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user
