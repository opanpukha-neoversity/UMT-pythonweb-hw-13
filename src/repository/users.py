"""Repository functions for working with users."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import User, UserRole
from src.schemas import UserCreate


class UserRepository:
    """Data access layer for users."""

    def __init__(self, db: Session):
        """Store the database session for repository operations."""

        self.db = db

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email or `None` when it does not exist."""

        return self.db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: int) -> User | None:
        """Return a user by its primary key."""

        return self.db.get(User, user_id)

    def create_user(self, body: UserCreate, hashed_password: str, role: UserRole = UserRole.USER) -> User:
        """Persist a newly registered user."""

        user = User(
            username=body.username,
            email=body.email,
            hashed_password=hashed_password,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def confirm_email(self, user: User) -> User:
        """Mark a user's email as confirmed."""

        user.confirmed = True
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_avatar(self, user: User, avatar_url: str) -> User:
        """Update the avatar URL for a user."""

        user.avatar_url = avatar_url
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user: User, hashed_password: str) -> User:
        """Replace a user's password hash."""

        user.hashed_password = hashed_password
        self.db.commit()
        self.db.refresh(user)
        return user
