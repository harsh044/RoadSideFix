# app/services/tracking_service.py

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
)


def get_provider_active_request(
    db: Session,
    provider_id: UUID,
) -> ServiceRequest | None:
    """
    Return the active ON_THE_WAY request assigned to this provider.
    """

    return db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.provider_id == provider_id,
            ServiceRequest.status == ServiceRequestStatus.ON_THE_WAY,
        )
    )


def customer_can_track_request(
    db: Session,
    customer_id: UUID,
    request_id: UUID,
) -> ServiceRequest | None:
    """
    Verify that the customer owns the service request and
    that the request is currently trackable.
    """

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.customer_id == customer_id,
        )
    )

    if request is None:
        return None

    allowed_statuses = {
        ServiceRequestStatus.ACCEPTED,
        ServiceRequestStatus.ON_THE_WAY,
        ServiceRequestStatus.ARRIVED,
        ServiceRequestStatus.IN_PROGRESS,
    }

    if request.status not in allowed_statuses:
        return None

    return request


def provider_can_update_request(
    db: Session,
    provider_id: UUID,
    request_id: UUID,
) -> ServiceRequest | None:
    """
    Verify that the request is assigned to this provider.
    """

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == request_id,
            ServiceRequest.provider_id == provider_id,
        )
    )

    if request is None:
        return None

    if request.status != ServiceRequestStatus.ON_THE_WAY:
        return None

    return request