from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.security.auth import (
    hash_password,
    verify_password,
)


def normalize_email(
    email: str,
) -> str:
    return email.strip().lower()


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    normalized_email = normalize_email(
        email,
    )

    result = db.execute(
        select(User).where(
            User.email == normalized_email,
        )
    )

    return result.scalar_one_or_none()


def create_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    user = User(
        email=normalize_email(
            email,
        ),
        password_hash=hash_password(
            password,
        ),
    )

    db.add(
        user,
    )

    db.flush()

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(
        db=db,
        email=email,
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user