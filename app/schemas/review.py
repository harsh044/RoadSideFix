# app/schemas/review.py

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)


class ReviewCreate(BaseModel):

    service_request_id: UUID

    rating: int = Field(
        ...,
        ge=1,
        le=5,
    )

    comment: str | None = Field(
        default=None,
        max_length=1000,
    )


class ReviewResponse(BaseModel):

    id: UUID

    service_request_id: UUID

    customer_id: UUID

    provider_id: UUID

    rating: int

    comment: str | None

    created_at: datetime