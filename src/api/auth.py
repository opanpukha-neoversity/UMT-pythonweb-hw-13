"""Authentication and email-verification routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository.users import UserRepository
from src.schemas import LoginRequest, PasswordResetConfirm, PasswordResetRequest, RequestEmail, Token, UserCreate, UserResponse
from src.services.auth import auth_service
from src.services.email import email_service

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(body: UserCreate, db: Session = Depends(get_db)):
    """Register a new user and send a verification email."""

    repo = UserRepository(db)
    existing_user = repo.get_by_email(body.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already exists')

    hashed_password = auth_service.get_password_hash(body.password)
    user = repo.create_user(body, hashed_password)
    token = auth_service.create_email_token(user.email)
    try:
        email_service.send_verification_email(user.email, token)
    except Exception:
        pass
    return user


@router.post('/login', response_model=Token, status_code=status.HTTP_201_CREATED)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user with email and password and return JWT."""

    repo = UserRepository(db)
    user = repo.get_by_email(body.username)
    if user is None or not auth_service.verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')

    access_token = auth_service.create_access_token(user.email)
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/verify-email/{token}')
def verify_email(token: str, db: Session = Depends(get_db)):
    """Confirm a user's email using a signed verification token."""

    email = auth_service.get_email_from_token(token, 'verify')
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    if user.confirmed:
        return {'message': 'Your email is already confirmed'}
    repo.confirm_email(user)
    return {'message': 'Email confirmed'}


@router.post('/request-email')
def request_email(body: RequestEmail, db: Session = Depends(get_db)):
    """Resend a verification email to an existing unconfirmed user."""

    repo = UserRepository(db)
    user = repo.get_by_email(body.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    if user.confirmed:
        return {'message': 'Your email is already confirmed'}
    token = auth_service.create_email_token(user.email)
    try:
        email_service.send_verification_email(user.email, token)
    except Exception:
        pass
    return {'message': 'Verification email sent'}


@router.post('/forgot-password')
def forgot_password(body: PasswordResetRequest, db: Session = Depends(get_db)):
    """Send a password reset email for an existing user."""

    repo = UserRepository(db)
    user = repo.get_by_email(body.email)

    if user:
        token = auth_service.create_reset_token(user.email, user.hashed_password)
        try:
            email_service.send_reset_email(user.email, token)
        except Exception:
            pass
    return {'message': 'If that email exists, a reset message has been sent'}

@router.get('/reset-password/{token}')
def verify_reset_password_token(token: str, db: Session = Depends(get_db)):
    """Validate password reset token before confirming password change."""

    payload = auth_service.decode_token(token)

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

    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )

    auth_service.verify_reset_token(token, user.hashed_password)

    return {'message': 'Reset token is valid'}

@router.post('/reset-password')
def reset_password(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Accept a reset token, validate it and replace the stored password hash."""

    payload = auth_service.decode_token(body.token)

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

    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )

    auth_service.verify_reset_token(body.token, user.hashed_password)

    if auth_service.verify_password(body.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='New password must be different from the current password',
        )

    repo.update_password(user, auth_service.get_password_hash(body.new_password))
    return {'message': 'Password updated successfully'}
