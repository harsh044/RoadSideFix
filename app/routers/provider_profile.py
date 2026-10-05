import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import require_role
from app.models.provider import ProviderProfile
from app.models.user import User, UserRole
from app.schemas.provider import (
    AvailabilityUpdate,
    LocationUpdate,
    ProviderProfileCreate,
    ProviderProfileResponse,
    ProviderProfileUpdate,
)
from geoalchemy2.shape import from_shape
from shapely.geometry import Point


router = APIRouter(
    prefix="/api/v1/provider/profile",
    tags=["Provider Profile"],
)


provider_required = require_role(
    UserRole.SERVICE_PROVIDER
)


@router.post(
    "",
    response_model=ProviderProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_provider_profile(
    data: ProviderProfileCreate,
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    existing_profile = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Provider profile already exists",
        )

    profile = ProviderProfile(
        user_id=current_user.id,
        business_name=data.business_name,
        description=data.description,
        phone=data.phone or current_user.phone,
        address=data.address,
        city=data.city,
        state=data.state,
        pincode=data.pincode,
        latitude=data.latitude,
        longitude=data.longitude,
        service_radius_km=data.service_radius_km,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


@router.get(
    "",
    response_model=ProviderProfileResponse,
)
def get_provider_profile(
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    profile = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found",
        )

    return profile


@router.put(
    "",
    response_model=ProviderProfileResponse,
)
def update_provider_profile(
    data: ProviderProfileUpdate,
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    profile = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile


@router.put(
    "/location",
    response_model=ProviderProfileResponse,
)
def update_location(
    data: LocationUpdate,
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    profile = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found",
        )

    profile.latitude = data.latitude
    profile.longitude = data.longitude
    # profile.location = from_shape(
    #     Point(
    #         data.longitude,
    #         data.latitude,
    #     ),
    #     srid=4326,
    # )

    db.commit()
    db.refresh(profile)

    return profile


@router.put(
    "/availability",
    response_model=ProviderProfileResponse,
)
def update_availability(
    data: AvailabilityUpdate,
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    profile = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found",
        )

    profile.is_available = data.is_available

    db.commit()
    db.refresh(profile)

    return profile