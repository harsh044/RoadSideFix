# app/routers/reviews.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.review import Review

from app.models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
)

from app.models.user import User

from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
)

from app.dependencies.auth import get_current_user
from sqlalchemy import func

from app.models.provider import ProviderProfile
from app.dependencies.auth import require_role
from app.models.user import User, UserRole

provider_required = require_role(
    UserRole.SERVICE_PROVIDER
)

router = APIRouter(
    prefix="/api/v1/reviews",
    tags=["Reviews"],
)


@router.post(
    "",
    response_model=ReviewResponse,
)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id
            == payload.service_request_id,

            ServiceRequest.customer_id
            == current_user.id,
        )
    )

    if request is None:
        raise HTTPException(
            status_code=404,
            detail="Service request not found",
        )

    if request.status != ServiceRequestStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Review can only be submitted after service completion",
        )

    if request.provider_id is None:
        raise HTTPException(
            status_code=400,
            detail="No provider assigned",
        )

    existing_review = db.scalar(
        select(Review).where(
            Review.service_request_id == request.id
        )
    )

    if existing_review:
        raise HTTPException(
            status_code=400,
            detail="Review already submitted",
        )

    review = Review(
        service_request_id=request.id,
        customer_id=current_user.id,
        provider_id=request.provider_id,
        rating=payload.rating,
        comment=payload.comment,
    )

    db.add(review)

    db.commit()

    db.refresh(review)

    return review

@router.get(
    "/provider/{provider_id}",
)
def get_provider_rating(
    provider_id: str,
    db: Session = Depends(get_db),
):

    result = db.execute(
        select(
            func.avg(Review.rating),
            func.count(Review.id),
        ).where(
            Review.provider_id == provider_id
        )
    ).one()

    average_rating = result[0]
    total_reviews = result[1]

    return {
        "provider_id": provider_id,
        "average_rating": (
            round(float(average_rating), 2)
            if average_rating is not None
            else 0
        ),
        "total_reviews": total_reviews,
    }

@router.get(
    "/provider/{provider_id}/list",
    response_model=list[ReviewResponse],
)
def get_provider_reviews(
    provider_id: str,
    db: Session = Depends(get_db),
):

    reviews = db.scalars(
        select(Review)
        .where(
            Review.provider_id == provider_id
        )
        .order_by(
            Review.created_at.desc()
        )
    ).all()

    return reviews

@router.get(
    "/history",
)
def customer_request_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    "/provider/history",
)
def provider_request_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(provider_required),
):

    provider = db.scalar(
        select(ProviderProfile).where(
            ProviderProfile.user_id
            == current_user.id
        )
    )

    if provider is None:
        raise HTTPException(
            status_code=404,
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