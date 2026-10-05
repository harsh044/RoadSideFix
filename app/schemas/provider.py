from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProviderProfileCreate(BaseModel):

    business_name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    phone: str | None = Field(
        default=None,
        min_length=10,
        max_length=20,
    )

    address: str | None = Field(
        default=None,
        max_length=255,
    )

    city: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    pincode: str | None = Field(
        default=None,
        max_length=10,
    )

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    service_radius_km: float = Field(
        default=10,
        gt=0,
        le=100,
    )


class ProviderProfileUpdate(BaseModel):

    business_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = None

    phone: str | None = None

    address: str | None = None

    city: str | None = None

    state: str | None = None

    pincode: str | None = None

    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    service_radius_km: float | None = Field(
        default=None,
        gt=0,
        le=100,
    )


class LocationUpdate(BaseModel):

    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )


class AvailabilityUpdate(BaseModel):

    is_available: bool


class ProviderProfileResponse(BaseModel):

    id: UUID
    user_id: UUID

    business_name: str
    description: str | None

    phone: str | None

    address: str | None
    city: str | None
    state: str | None
    pincode: str | None

    latitude: float | None
    longitude: float | None

    service_radius_km: float

    is_available: bool
    is_verified: bool

    created_at: datetime
    updated_at: datetime | None

    model_config = {
        "from_attributes": True
    }