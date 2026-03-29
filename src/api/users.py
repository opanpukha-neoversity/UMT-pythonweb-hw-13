"""User profile routes, including avatar management and rate limiting."""

from collections import defaultdict, deque
from time import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.database.models import User
from src.database.db import get_db
from sqlalchemy.orm import Session
from src.repository.users import UserRepository
from src.schemas import UserResponse, UserRoleUpdate
from src.services.auth import get_current_user, require_admin
from src.services.cache import get_redis_client, user_cache_key
from src.services.cloudinary_service import cloudinary_service

router = APIRouter(prefix='/api/users', tags=['users'])
_request_log: dict[int, deque[float]] = defaultdict(deque)
MAX_ME_REQUESTS = 5
WINDOW_SECONDS = 60



def me_rate_limit(current_user: User = Depends(get_current_user)) -> User:
    """Allow only a fixed number of `/me` requests per minute per user."""

    now = time()
    history = _request_log[current_user.id]
    while history and now - history[0] > WINDOW_SECONDS:
        history.popleft()
    if len(history) >= MAX_ME_REQUESTS:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Too many requests')
    history.append(now)
    return current_user


@router.get('/me', response_model=UserResponse)
def read_me(current_user: User = Depends(me_rate_limit)):
    """Return the authenticated user's profile."""

    return current_user


@router.patch('/avatar', response_model=UserResponse)
def update_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a custom avatar for the authenticated user."""

    avatar_url = cloudinary_service.upload_avatar(file, current_user.id)
    user = UserRepository(db).update_avatar(current_user, avatar_url)
    get_redis_client().delete(user_cache_key(user.id))
    return user


@router.patch('/default-avatar', response_model=UserResponse)
def update_default_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Allow only admins to change their own default avatar."""

    avatar_url = cloudinary_service.upload_avatar(file, current_user.id)
    user = UserRepository(db).update_avatar(current_user, avatar_url)
    get_redis_client().delete(user_cache_key(user.id))
    return user

@router.patch(
    '/{user_id}/role',
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
def change_user_role(
    user_id: int,
    body: UserRoleUpdate,
    db: Session = Depends(get_db),
):
    """Allow only admins to change another user's role."""

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )

    updated_user = repo.update_role(user, body.role)
    get_redis_client().delete(user_cache_key(updated_user.id))
    return updated_user
