"""Pydantic schemas for request and response models."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.database.models import UserRole


class ContactBase(BaseModel):
    """Shared contact fields and validation rules."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone_number: str = Field(min_length=7, max_length=30)
    birthday: date
    additional_data: str | None = Field(default=None, max_length=2000)

    @field_validator('first_name', 'last_name', 'phone_number')
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        """Trim surrounding spaces and reject blank strings."""

        value = value.strip()
        if not value:
            raise ValueError('Field cannot be blank')
        return value

    @field_validator('birthday')
    @classmethod
    def validate_birthday(cls, value: date) -> date:
        """Ensure that birthday is not in the future."""

        if value > date.today():
            raise ValueError('Birthday cannot be in the future')
        return value


class ContactCreate(ContactBase):
    """Schema used to create a contact."""


class ContactUpdate(BaseModel):
    """Schema used to partially update a contact."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=7, max_length=30)
    birthday: date | None = None
    additional_data: str | None = Field(default=None, max_length=2000)


class ContactResponse(ContactBase):
    """Serialized contact for API responses."""

    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """Payload used during registration."""

    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    """Public user information returned by the API."""

    id: int
    username: str
    email: EmailStr
    avatar_url: str | None = None
    confirmed: bool
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = 'bearer'


class LoginRequest(BaseModel):
    """JSON login payload."""

    username: EmailStr
    password: str


class RequestEmail(BaseModel):
    """Request payload for sending a verification email again."""

    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Request payload for initiating a password reset flow."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Request payload for confirming a password reset."""

    token: str
    new_password: str = Field(min_length=6, max_length=128)
