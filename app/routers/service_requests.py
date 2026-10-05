import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import require_role
from app.models.provider import ProviderProfile
from app.models.provider_service import ProviderService
from app.models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
)
from app.models.provider_location import ProviderLocation
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.schemas.service_request import (
    ServiceRequestCreate,
    ServiceRequestResponse,
    CompleteServiceRequest,
    ServiceRequestCancel,
)
from datetime import datetime, timezone
from app.dependencies.auth import (
    get_current_user,
    require_role,
)
from sqlalchemy import text

from geoalchemy2.shape import to_shape

from app.models.provider_location import (
    ProviderLocation,
)
from app.services.tracking_service import (
    customer_can_track_request,
)

from app.services.service_request_service import (
    validate_customer_cancellation,
)

from app.models.provider import ProviderProfile

router = APIRouter(
    prefix="/api/v1/service-requests",
    tags=["Service Requests"],
)

customer_required = require_role(
    UserRole.CUSTOMER
)

provider_required = require_role(
    UserRole.SERVICE_PROVIDER
)

@router.post(
    "",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service_request(
    data: ServiceRequestCreate,
    current_user: User = Depends(customer_required),
    db: Session = Depends(get_db),
):

    # ----------------------------------
    # Check vehicle belongs to customer
    # ----------------------------------
    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == data.vehicle_id,
            Vehicle.customer_id == current_user.id,
        )
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    # ----------------------------------
    # Check provider exists and available
    # ----------------------------------
    provider = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.id == data.provider_id,
            ProviderProfile.is_available.is_(True),
        )
    )

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider is not available",
        )

    # ----------------------------------
    # Validate service
    # ----------------------------------
    estimated_price = None

    if data.service_id:

        service = db.scalar(
            select(ProviderService).where(
                ProviderService.id == data.service_id,
                ProviderService.provider_id == provider.id,
                ProviderService.is_active.is_(True),
            )
        )

        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service not found for this provider",
            )

        estimated_price = service.base_price

    # ----------------------------------
    # Create service request
    # ----------------------------------
    request = ServiceRequest(
        customer_id=current_user.id,
        provider_id=provider.id,
        vehicle_id=vehicle.id,
        service_id=data.service_id,

        status=ServiceRequestStatus.PENDING,

        problem_description=data.problem_description,
        customer_address=data.customer_address,

        # Store customer coordinates directly
        latitude=data.latitude,
        longitude=data.longitude,

        estimated_price=estimated_price,
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return request

@router.get(
    "/customer",
    response_model=list[ServiceRequestResponse],
)
def get_customer_requests(
    current_user: User = Depends(customer_required),
    db: Session = Depends(get_db),
):

    requests = db.scalars(
        select(ServiceRequest)
        .where(
            ServiceRequest.customer_id
            == current_user.id
        )
        .order_by(
            ServiceRequest.created_at.desc()
        )
    ).all()

    return requests

@router.get(
    "/provider",
    response_model=list[ServiceRequestResponse],
)
def get_provider_requests(
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

    requests = db.scalars(
        select(ServiceRequest)
        .where(
            ServiceRequest.provider_id
            == provider.id
        )
        .order_by(
            ServiceRequest.created_at.desc()
        )
    ).all()

    return requests

@router.patch(
    "/{request_id}/accept",
    response_model=ServiceRequestResponse,
)
def accept_request(
    request_id: uuid.UUID,
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

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.provider_id == provider.id,
        )
    )

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found",
        )

    if request.status != ServiceRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only pending requests can be accepted"
            ),
        )

    request.status = ServiceRequestStatus.ACCEPTED

    request.accepted_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(request)

    return request

@router.patch(
    "/{request_id}/reject",
    response_model=ServiceRequestResponse,
)
def reject_request(
    request_id: uuid.UUID,
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

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.provider_id == provider.id,
        )
    )

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found",
        )

    if request.status != ServiceRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only pending requests can be rejected"
            ),
        )

    request.status = ServiceRequestStatus.REJECTED

    db.commit()
    db.refresh(request)

    return request

@router.patch(
    "/{request_id}/on-the-way",
    response_model=ServiceRequestResponse,
)
def provider_on_the_way(
    request_id: uuid.UUID,
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

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.provider_id == provider.id,
        )
    )

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found",
        )

    if request.status != ServiceRequestStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request must be accepted first",
        )

    request.status = ServiceRequestStatus.ON_THE_WAY

    db.commit()
    db.refresh(request)

    return request

@router.patch(
    "/{request_id}/arrived",
    response_model=ServiceRequestResponse,
)
def provider_arrived(
    request_id: uuid.UUID,
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
            status_code=404,
            detail="Provider profile not found",
        )

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.provider_id == provider.id,
        )
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Service request not found",
        )

    if request.status != ServiceRequestStatus.ON_THE_WAY:
        raise HTTPException(
            status_code=400,
            detail="Provider must be on the way first",
        )

    request.status = ServiceRequestStatus.ARRIVED

    db.commit()
    db.refresh(request)

    return request

@router.patch(
    "/{request_id}/start",
    response_model=ServiceRequestResponse,
)
def start_repair(
    request_id: uuid.UUID,
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    provider = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id == current_user.id
        )
    )

    if not provider:
        raise HTTPException(
            status_code=404,
            detail="Provider profile not found",
        )

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.provider_id == provider.id,
        )
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Service request not found",
        )

    if request.status != ServiceRequestStatus.ARRIVED:
        raise HTTPException(
            status_code=400,
            detail="Provider must arrive first",
        )

    request.status = ServiceRequestStatus.IN_PROGRESS

    db.commit()
    db.refresh(request)

    return request

@router.patch(
    "/{request_id}/complete",
    response_model=ServiceRequestResponse,
)
def complete_request(
    request_id: uuid.UUID,
    data: CompleteServiceRequest,
    current_user: User = Depends(provider_required),
    db: Session = Depends(get_db),
):

    provider = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id == current_user.id
        )
    )

    if not provider:
        raise HTTPException(
            status_code=404,
            detail="Provider profile not found",
        )

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.provider_id == provider.id,
        )
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Service request not found",
        )

    if request.status != ServiceRequestStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail="Repair must be in progress first",
        )

    request.status = ServiceRequestStatus.COMPLETED

    request.final_price = data.final_price

    request.provider_note = data.provider_note

    request.completed_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(request)

    return request

@router.patch(
    "/{request_id}/cancel",
    response_model=ServiceRequestResponse,
)
def cancel_request(
    request_id: uuid.UUID,
    data: ServiceRequestCancel,
    current_user: User = Depends(customer_required),
    db: Session = Depends(get_db),
):

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.customer_id
            == current_user.id,
        )
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Service request not found",
        )

    allowed_statuses = {
        ServiceRequestStatus.PENDING,
        ServiceRequestStatus.ACCEPTED,
        ServiceRequestStatus.ON_THE_WAY,
    }

    if request.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Request cannot be cancelled now",
        )

    request.status = ServiceRequestStatus.CANCELLED

    request.cancellation_reason = data.reason

    db.commit()
    db.refresh(request)

    return request

@router.get(
    "/{request_id}",
    response_model=ServiceRequestResponse,
)
def get_service_request(
    request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id
        )
    )

    if not request:
        raise HTTPException(
            status_code=404,
            detail="Service request not found",
        )

    if current_user.role == UserRole.CUSTOMER:

        if request.customer_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied",
            )

    elif current_user.role == UserRole.SERVICE_PROVIDER:

        provider = db.scalar(
            select(ProviderProfile).where(
                ProviderProfile.user_id
                == current_user.id
            )
        )

        if (
            not provider
            or request.provider_id != provider.id
        ):
            raise HTTPException(
                status_code=403,
                detail="Access denied",
            )

    else:
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    return request

@router.get(
    "/{request_id}/provider-location",
)
def get_provider_location(

    request_id: uuid.UUID,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db),
):

    # =====================================================
    # SECURITY CHECK
    #
    # request.customer_id == current_user.id
    # =====================================================

    request = customer_can_track_request(
        db=db,
        customer_id=current_user.id,
        request_id=request_id,
    )

    if not request:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You are not authorized "
                "to track this service request"
            ),
        )

    # =====================================================
    # Get provider location
    # =====================================================

    provider_location = db.scalar(
        select(ProviderLocation).where(
            ProviderLocation.provider_id
            == request.provider_id
        )
    )

    if not provider_location:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider location unavailable",
        )

    # =====================================================
    # Convert PostGIS → Point
    # =====================================================

    point = to_shape(
        provider_location.location
    )

    return {
        "request_id": str(
            request.id
        ),

        "provider_id": str(
            request.provider_id
        ),

        "latitude": point.y,

        "longitude": point.x,

        "last_seen_at": (
            provider_location
            .last_seen_at
        ),
    }

@router.put(
    "/{request_id}/cancel",
)
def cancel_service_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.customer_id == current_user.id,
        )
    )

    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found",
        )

    validate_customer_cancellation(
        request.status
    )

    request.status = ServiceRequestStatus.CANCELLED

    db.commit()

    return {
        "message": "Service request cancelled",
        "request_id": str(request.id),
        "status": request.status,
    }

@router.put(
    "/{request_id}/reject",
)
def reject_service_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider = db.scalar(
    select(ProviderProfile).where(
        ProviderProfile.user_id == current_user.id
    )
    )

    if provider is None:
        raise HTTPException(
            status_code=404,
            detail="Provider profile not found",
        )

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.provider_id == provider.id,
        )
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found",
        )

    if request.status != ServiceRequestStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="Only pending requests can be rejected",
        )

    request.status = ServiceRequestStatus.REJECTED

    db.commit()

    return {
        "message": "Service request rejected",
        "request_id": str(request.id),
        "status": request.status,
    }