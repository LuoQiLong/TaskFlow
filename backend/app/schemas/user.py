from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    display_name: str | None = None
    is_active: bool = True
    avatar_url: str | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    id: int
    email: str
    token: str
    role: str = "member"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)


class ForgotPasswordResponse(BaseModel):
    message: str


# ── Admin / user management ──

class UserListItem(BaseModel):
    id: int
    email: str
    role: str
    display_name: str | None = None
    is_active: bool = True
    avatar_url: str | None = None
    created_at: str | None = None


class UserUpdateRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None
    display_name: str | None = None


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)
