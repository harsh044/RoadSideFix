from datetime import datetime

from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)


class ProviderLocationUpdate(BaseModel):

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
    )


class ProviderLocationResponse(BaseModel):

    provider_id: UUID

    request_id: UUID | None = None

    latitude: float

    longitude: float

    last_seen_at: datetime