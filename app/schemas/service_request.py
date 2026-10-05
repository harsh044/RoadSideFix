from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.service_request import ServiceRequestStatus


class ServiceRequestCreate(BaseModel):

    provider_id: UUID

    vehicle_id: UUID

    service_id: UUID | None = None

    problem_description: str = Field(
        min_length=5,
        max_length=2000,
    )

    customer_address: str | None = Field(
        default=None,
        max_length=255,
    )

    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )


class ServiceRequestResponse(BaseModel):

    id: UUID

    customer_id: UUID
    provider_id: UUID
    vehicle_id: UUID

    service_id: UUID | None

    status: ServiceRequestStatus

    problem_description: str

    customer_address: str | None

    latitude: float
    longitude: float

    estimated_price: float | None
    final_price: float | None

    provider_note: str | None

    cancellation_reason: str | None

    created_at: datetime
    updated_at: datetime

    accepted_at: datetime | None
    completed_at: datetime | None

class ServiceRequestStatusUpdate(BaseModel):

    status: ServiceRequestStatus

    provider_note: str | None = Field(
        default=None,
        max_length=2000,
    )

class ServiceRequestCancel(BaseModel):

    reason: str = Field(
        min_length=3,
        max_length=500,
        description="Reason for cancelling the service request",
    )

class CompleteServiceRequest(BaseModel):

    final_price: float = Field(
        ge=0
    )

    provider_note: str | None = Field(
        default=None,
        max_length=2000,
    )