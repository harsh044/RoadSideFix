import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import require_role
from app.models.provider import ProviderProfile
from app.models.provider_service import ProviderService
from app.models.user import User, UserRole
from app.schemas.provider_service import (
    ProviderServiceCreate,
    ProviderServiceResponse,
    ProviderServiceUpdate,
)


router = APIRouter(
    prefix="/api/v1/provider/services",
    tags=["Provider Services"],
)


provider_required = require_role(
    UserRole.SERVICE_PROVIDER
)

@router.post(
    "",
    response_model=ProviderServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service(
    data: ProviderServiceCreate,
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    provider = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Create provider profile first",
        )

    service = ProviderService(
        provider_id=provider.id,
        name=data.name,
        description=data.description,
        base_price=data.base_price,
    )

    db.add(service)
    db.commit()
    db.refresh(service)

    return service

@router.get(
    "",
    response_model=list[ProviderServiceResponse],
)
def get_services(
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    provider = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found",
        )

    services = db.scalars(
        select(ProviderService)
        .where(
            ProviderService.provider_id
            == provider.id
        )
        .order_by(
            ProviderService.created_at.desc()
        )
    ).all()

    return services

@router.put(
    "/{service_id}",
    response_model=ProviderServiceResponse,
)
def update_service(
    service_id: uuid.UUID,
    data: ProviderServiceUpdate,
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    provider = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found",
        )

    service = db.scalar(
        select(ProviderService).where(
            ProviderService.id == service_id,
            ProviderService.provider_id
            == provider.id,
        )
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)

    return service

@router.delete(
    "/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_service(
    service_id: uuid.UUID,
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    provider = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found",
        )

    service = db.scalar(
        select(ProviderService).where(
            ProviderService.id == service_id,
            ProviderService.provider_id
            == provider.id,
        )
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    db.delete(service)
    db.commit()

    return None

