from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.vehicle import FuelType, VehicleType


class VehicleCreate(BaseModel):

    vehicle_type: VehicleType

    brand: str = Field(
        min_length=2,
        max_length=100,
    )

    model: str = Field(
        min_length=1,
        max_length=100,
    )

    registration_number: str = Field(
        min_length=3,
        max_length=30,
    )

    year: int | None = Field(
        default=None,
        ge=1900,
        le=2100,
    )

    fuel_type: FuelType | None = None

    color: str | None = Field(
        default=None,
        max_length=50,
    )


class VehicleUpdate(BaseModel):

    vehicle_type: VehicleType | None = None

    brand: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    model: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    registration_number: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
    )

    year: int | None = Field(
        default=None,
        ge=1900,
        le=2100,
    )

    fuel_type: FuelType | None = None

    color: str | None = Field(
        default=None,
        max_length=50,
    )


class VehicleResponse(BaseModel):

    id: UUID
    customer_id: UUID

    vehicle_type: VehicleType
    brand: str
    model: str
    registration_number: str

    year: int | None
    fuel_type: FuelType | None
    color: str | None

    created_at: datetime
    updated_at: datetime | None

    model_config = {
        "from_attributes": True
    }