# app/routers/provider_location.py

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.provider_location import ProviderLocation
from app.models.provider import ProviderProfile
from app.models.user import User, UserRole
from app.schemas.provider_location import (
    ProviderLocationResponse,
    ProviderLocationUpdate,
)
from app.services.tracking_pubsub import publish_tracking_event
from app.services.tracking_service import get_provider_active_request
from app.dependencies.auth import get_current_user
from app.dependencies.auth import require_role


router = APIRouter(
    prefix="/api/v1/providers",
    tags=["Provider Location"],
)


provider_required = require_role(UserRole.SERVICE_PROVIDER)


@router.put(
    "/location",
    response_model=ProviderLocationResponse,
)
async def update_provider_location(
    payload: ProviderLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(provider_required),
):
    """
    Update the authenticated provider's current GPS location.

    The provider cannot select another provider or request manually.
    The request is determined from the authenticated provider account.
    """

    provider_profile = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id == current_user.id
        )
    )

    if provider_profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found",
        )

    active_request = get_provider_active_request(
        db=db,
        provider_id=provider_profile.id,
    )

    if active_request is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You do not have an active service request",
        )

    point = Point(
        payload.longitude,
        payload.latitude,
    )

    location_geometry = from_shape(
        point,
        srid=4326,
    )

    provider_location = db.scalar(
        select(ProviderLocation).where(
            ProviderLocation.provider_id == provider_profile.id
        )
    )

    if provider_location is None:
        provider_location = ProviderLocation(
            provider_id=provider_profile.id,
            location=location_geometry,
        )

        db.add(provider_location)

    else:
        provider_location.location = location_geometry

    db.commit()
    db.refresh(provider_location)

    event = {
        "type": "provider_location_updated",
        "request_id": str(active_request.id),
        "provider_id": str(provider_profile.id),
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "last_seen_at": (
            provider_location.last_seen_at.isoformat()
            if provider_location.last_seen_at
            else None
        ),
    }

    await publish_tracking_event(
        request_id=active_request.id,
        event=event,
    )

    return ProviderLocationResponse(
        provider_id=provider_profile.id,
        request_id=active_request.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        last_seen_at=provider_location.last_seen_at,
    )