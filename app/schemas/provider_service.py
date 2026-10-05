from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProviderServiceCreate(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    base_price: float = Field(
        default=0,
        ge=0,
    )


class ProviderServiceUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    base_price: float | None = Field(
        default=None,
        ge=0,
    )

    is_active: bool | None = None


class ProviderServiceResponse(BaseModel):

    id: UUID
    provider_id: UUID

    name: str
    description: str | None
    base_price: float
    is_active: bool

    created_at: datetime
    updated_at: datetime | None

    model_config = {
        "from_attributes": True
    }