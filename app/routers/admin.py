from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.dependencies.admin import get_current_admin
from app.models.payment import Payment
from app.models.provider import ProviderProfile
from app.models.review import Review
from app.models.service_request import ServiceRequest, ServiceRequestStatus
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminDashboardResponse,
    AdminPaymentResponse,
    AdminProviderResponse,
    AdminServiceRequestResponse,
    AdminUserResponse,
    AdminCreate,
    AdminResponse,
)
from app.core.security import hash_password

from app.dependencies.auth import get_current_user
from app.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"],
)

@router.post(
    "/create",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin(
    data: AdminCreate,
    db: Session = Depends(get_db),
):

    # Only existing admin can create another admin
    # if current_user.role != "admin":
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Only admin can create another admin",
    #     )

    # Check existing email
    existing_user = db.scalar(
        select(User).where(
            User.email == data.email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check existing phone
    existing_phone = db.scalar(
        select(User).where(
            User.phone == data.phone
        )
    )

    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone already registered",
        )

    admin = User(
        id=uuid.uuid4(),
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role="admin",
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin
# =========================================================
# DASHBOARD
# =========================================================

@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
)
def admin_dashboard(
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()

    try:
        total_users = db.scalar(
            select(func.count(User.id))
        ) or 0

        total_customers = db.scalar(
            select(func.count(User.id)).where(
                User.role == UserRole.CUSTOMER
            )
        ) or 0

        total_providers = db.scalar(
            select(func.count(User.id)).where(
                User.role == UserRole.SERVICE_PROVIDER
            )
        ) or 0

        total_admins = db.scalar(
            select(func.count(User.id)).where(
                User.role == UserRole.ADMIN
            )
        ) or 0

        active_users = db.scalar(
            select(func.count(User.id)).where(
                User.is_active.is_(True)
            )
        ) or 0

        inactive_users = db.scalar(
            select(func.count(User.id)).where(
                User.is_active.is_(False)
            )
        ) or 0

        total_requests = db.scalar(
            select(func.count(ServiceRequest.id))
        ) or 0

        pending_requests = db.scalar(
            select(func.count(ServiceRequest.id)).where(
                ServiceRequest.status == ServiceRequestStatus.PENDING
            )
        ) or 0

        accepted_requests = db.scalar(
            select(func.count(ServiceRequest.id)).where(
                ServiceRequest.status == ServiceRequestStatus.ACCEPTED
            )
        ) or 0

        completed_requests = db.scalar(
            select(func.count(ServiceRequest.id)).where(
                ServiceRequest.status == ServiceRequestStatus.COMPLETED
            )
        ) or 0

        cancelled_requests = db.scalar(
            select(func.count(ServiceRequest.id)).where(
                ServiceRequest.status == ServiceRequestStatus.CANCELLED
            )
        ) or 0

        total_payments = db.scalar(
            select(func.count(Payment.id))
        ) or 0

        successful_payments = db.scalar(
            select(func.count(Payment.id)).where(
                Payment.status == "SUCCESS"
            )
        ) or 0

        failed_payments = db.scalar(
            select(func.count(Payment.id)).where(
                Payment.status == "FAILED"
            )
        ) or 0

        total_reviews = db.scalar(
            select(func.count(Review.id))
        ) or 0

        return AdminDashboardResponse(
            total_users=total_users,
            total_customers=total_customers,
            total_providers=total_providers,
            total_admins=total_admins,
            active_users=active_users,
            inactive_users=inactive_users,

            total_service_requests=total_requests,
            pending_requests=pending_requests,
            accepted_requests=accepted_requests,
            completed_requests=completed_requests,
            cancelled_requests=cancelled_requests,

            total_payments=total_payments,
            successful_payments=successful_payments,
            failed_payments=failed_payments,

            total_reviews=total_reviews,
        )

    finally:
        db.close()

@router.get(
    "/users",
    response_model=list[AdminUserResponse],
)
def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: UserRole | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()

    try:
        query = select(User)

        if role:
            query = query.where(
                User.role == role
            )

        if is_active is not None:
            query = query.where(
                User.is_active == is_active
            )

        if search:
            search_value = f"%{search}%"

            query = query.where(
                (User.name.ilike(search_value))
                | (User.email.ilike(search_value))
                | (User.phone.ilike(search_value))
            )

        query = (
            query
            .order_by(User.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        users = db.scalars(query).all()

        return users

    finally:
        db.close()

@router.get(
    "/users/{user_id}",
    response_model=AdminUserResponse,
)
def get_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.id == user_id
            )
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    finally:
        db.close()@router.put(
    "/users/{user_id}/status",
    response_model=AdminUserResponse,
)
def update_user_status(
    user_id: UUID,
    is_active: bool,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.id == user_id
            )
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Prevent admin from disabling their own account
        if user.id == admin.id and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own admin account",
            )

        user.is_active = is_active

        db.commit()
        db.refresh(user)

        return user

    finally:
        db.close()

@router.get(
    "/providers",
    response_model=list[AdminProviderResponse],
)
def get_all_providers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()

    try:
        query = select(ProviderProfile)

        if search:
            search_value = f"%{search}%"

            query = query.where(
                (ProviderProfile.business_name.ilike(search_value))
                | (ProviderProfile.phone.ilike(search_value))
                | (ProviderProfile.address.ilike(search_value))
            )

        query = (
            query
            .order_by(ProviderProfile.business_name.asc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        providers = db.scalars(query).all()

        return providers

    finally:
        db.close()

@router.get(
    "/service-requests",
    response_model=list[AdminServiceRequestResponse],
)
def get_all_service_requests(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    request_status: ServiceRequestStatus | None = None,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()

    try:
        query = select(ServiceRequest)

        if request_status:
            query = query.where(
                ServiceRequest.status == request_status
            )

        query = (
            query
            .order_by(ServiceRequest.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        requests = db.scalars(query).all()

        return requests

    finally:
        db.close()

@router.get(
    "/payments",
    response_model=list[AdminPaymentResponse],
)
def get_all_payments(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    payment_status: str | None = None,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()

    try:
        query = select(Payment)

        if payment_status:
            query = query.where(
                Payment.status == payment_status
            )

        query = (
            query
            .order_by(Payment.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        payments = db.scalars(query).all()

        return payments

    finally:
        db.close()

@router.delete(
    "/reviews/{review_id}",
)
def delete_review(
    review_id: UUID,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()

    try:
        review = db.scalar(
            select(Review).where(
                Review.id == review_id
            )
        )

        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        db.delete(review)
        db.commit()

        return {
            "success": True,
            "message": "Review deleted successfully",
        }

    finally:
        db.close()

@router.get(
    "/service-requests/{request_id}",
    response_model=AdminServiceRequestResponse,
)
def get_service_request(
    request_id: UUID,
    admin: User = Depends(get_current_admin),
):
    db = SessionLocal()

    try:
        service_request = db.scalar(
            select(ServiceRequest).where(
                ServiceRequest.id == request_id
            )
        )

        if not service_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service request not found",
            )

        return service_request

    finally:
        db.close()

