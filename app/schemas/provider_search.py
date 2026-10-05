from uuid import UUID

from pydantic import BaseModel


class NearbyService(BaseModel):

    id: UUID
    name: str
    description: str | None
    base_price: float


class NearbyProviderResponse(BaseModel):

    provider_id: UUID
    business_name: str

    description: str | None

    address: str | None
    city: str | None

    latitude: float
    longitude: float

    distance_km: float

    is_available: bool
    is_verified: bool

    services: list[NearbyService]