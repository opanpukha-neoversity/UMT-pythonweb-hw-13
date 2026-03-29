"""Authentication helpers: password hashing, JWT and current-user resolution."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from src.conf.config import get_settings
from src.database.db import get_db
from src.database.models import User, UserRole
from src.repository.users import UserRepository
from src.services.cache import get_redis_client, serialize_user, user_cache_key

settings = get_settings()
password_hash = PasswordHash.recommended()
security = HTTPBearer(auto_error=False)


class AuthService:
    """Security service that manages passwords and JWT tokens."""

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Compare a plain password against a password hash."""

        return password_hash.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a plain-text password before storing it."""

        return password_hash.hash(password)

    def _create_token(self, data: dict, expires_minutes: int) -> str:
        """Build a signed JWT with an expiration timestamp."""

        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        to_encode.update({'exp': expire})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    def create_access_token(self, user_email: str) -> str:
        """Create an access token for API authorization."""

        return self._create_token({'sub': user_email, 'scope': 'access'}, settings.access_token_expire_minutes)

    def create_email_token(self, user_email: str) -> str:
        """Create a short-lived email verification token."""

        return self._create_token({'sub': user_email, 'scope': 'verify'}, settings.verify_token_expire_minutes)

    def create_reset_token(self, user_email: str, password_hash: str) -> str:
        """Create a short-lived password reset token."""

        return self._create_token({'sub': user_email, 'scope': 'reset', 'pwd': password_hash}, settings.reset_token_expire_minutes)

    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token payload."""

        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token') from exc

    def get_email_from_token(self, token: str, expected_scope: str) -> str:
        """Extract email from a token and validate its scope."""

        payload = self.decode_token(token)
        if payload.get('scope') != expected_scope or payload.get('sub') is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token scope')
        return payload['sub']

    def verify_reset_token(self, token: str, password_hash: str) -> str:
        """Validate a reset token, ensure it matches current password hash and return email."""

        payload = self.decode_token(token)

        if payload.get('scope') != 'reset':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token scope',
            )

        email = payload.get('sub')
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Invalid token payload',
            )

        if payload.get('pwd') != password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Reset token is no longer valid',
            )

        return email


auth_service = AuthService()



def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Return the authenticated user, using Redis cache before hitting the database."""

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    token = credentials.credentials
    email = auth_service.get_email_from_token(token, 'access')
    repo = UserRepository(db)
    cache = get_redis_client()

    user = repo.get_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    key = user_cache_key(user.id)
    cached = cache.get(key)
    if cached:
        data = json.loads(cached)
        user.username = data['username']
        user.email = data['email']
        user.avatar_url = data.get('avatar_url')
        user.confirmed = data['confirmed']
        user.role = UserRole(data['role'])
        return user

    cache.setex(key, settings.redis_user_cache_ttl, serialize_user(user))
    return user



def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Guard endpoint access to administrators only."""

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin role required')
    return current_user
