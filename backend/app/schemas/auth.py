import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import StrictRequestModel


class SignupRequest(StrictRequestModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}

    @field_validator("role", mode="before")
    @classmethod
    def _role_name(cls, value: object) -> object:
        return getattr(value, "name", value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class RefreshRequest(StrictRequestModel):
    refresh_token: str | None = None


class PasswordResetRequest(StrictRequestModel):
    email: EmailStr


class PasswordResetRequestResponse(BaseModel):
    message: str
    reset_token: str | None = None


class PasswordResetConfirm(StrictRequestModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdateProfileRequest(StrictRequestModel):
    full_name: str = Field(min_length=1, max_length=255)


class ChangePasswordRequest(StrictRequestModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UpdateUserRoleRequest(StrictRequestModel):
    role: str = Field(pattern="^(admin|agent|viewer)$")
