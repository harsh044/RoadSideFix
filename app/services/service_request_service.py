# app/services/service_request_service.py

from fastapi import HTTPException, status

from app.models.service_request import ServiceRequestStatus


def validate_customer_cancellation(
    current_status: ServiceRequestStatus,
) -> None:

    allowed_statuses = {
        ServiceRequestStatus.PENDING,
        ServiceRequestStatus.ACCEPTED,
    }

    if current_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Service request cannot be cancelled "
                "after provider has started travelling"
            ),
        )


def validate_provider_acceptance(
    current_status: ServiceRequestStatus,
) -> None:

    if current_status != ServiceRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be accepted",
        )


def validate_on_the_way(
    current_status: ServiceRequestStatus,
) -> None:

    if current_status != ServiceRequestStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request must be accepted before travelling",
        )


def validate_arrived(
    current_status: ServiceRequestStatus,
) -> None:

    if current_status != ServiceRequestStatus.ON_THE_WAY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must be on the way",
        )


def validate_start_service(
    current_status: ServiceRequestStatus,
) -> None:

    if current_status != ServiceRequestStatus.ARRIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must arrive before starting service",
        )


def validate_complete_service(
    current_status: ServiceRequestStatus,
) -> None:

    if current_status != ServiceRequestStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service must be in progress before completion",
        )