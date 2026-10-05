from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr | None = None

    phone: str = Field(
        min_length=10,
        max_length=20,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    role: UserRole


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr | None
    phone: str
    role: UserRole
    is_active: bool

    model_config = {
        "from_attributes": True
    }