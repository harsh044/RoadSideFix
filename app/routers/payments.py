# app/routers/payments.py

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

from app.models.payment import Payment
from app.models.service_request import (
    ServiceRequest,
    ServiceRequestStatus,
)
from app.models.user import User

from app.schemas.payment import (
    PaymentCreate,
    PaymentOrderResponse,
    PaymentResponse,
    PaymentVerify,
)

from app.services.razorpay_service import (
    create_razorpay_order,
    verify_payment_signature,
)

from app.dependencies.auth import get_current_user
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
templates = Jinja2Templates(
    directory="app/templates"
)

router = APIRouter(
    prefix="/api/v1/payments",
    tags=["Payments"],
)

@router.get(
    "/test/{service_request_id}",
    response_class=HTMLResponse,
)
def payment_test_page(
    service_request_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    context = {
        "request": request,
        "service_request_id": service_request_id,
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkNzYyMTVmYy00MjAxLTRkYTAtODQwOC1mZDE2YTg0Y2I4ODQiLCJyb2xlIjoiY3VzdG9tZXIiLCJ0eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzkwMDYxMTQ2fQ.qZQawPs8O2JJ00ID69qORwcpvx-Q75Hzhc-D7qwloUE",
    }

    return templates.TemplateResponse(
        request=request,
        name="payment.html",
        context=context,
    )


@router.post(
    "/create-order",
    response_model=PaymentOrderResponse,
)
def create_payment_order(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    request = db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.id == payload.service_request_id,
            ServiceRequest.customer_id == current_user.id,
        )
    )

    if request is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service request not found",
        )

    if request.status != ServiceRequestStatus.COMPLETED:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment can only be created after provider accepts the request",
        )

    existing_payment = db.scalar(
        select(Payment).where(
            Payment.service_request_id == request.id
        )
    )

    if existing_payment:

        if existing_payment.status == "SUCCESS":

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment already completed",
            )

        if existing_payment.razorpay_order_id:

            return PaymentOrderResponse(
                payment_id=existing_payment.id,
                service_request_id=existing_payment.service_request_id,
                razorpay_order_id=existing_payment.razorpay_order_id,
                razorpay_key_id=settings.razorpay_key_id,
                amount=existing_payment.amount,
                currency=existing_payment.currency,
                status=existing_payment.status,
            )

    # Replace this with your actual service pricing calculation.
    amount = Decimal(request.final_price)

    amount_in_rupees = int(amount)

    order = create_razorpay_order(
        amount_in_rupees=amount_in_rupees,
        receipt=str(request.id),
    )

    payment = existing_payment

    if payment is None:

        payment = Payment(
            service_request_id=request.id,
            customer_id=current_user.id,
            amount=amount,
            currency="INR",
            status="CREATED",
            razorpay_order_id=order["id"],
        )

        db.add(payment)

    else:

        payment.amount = amount
        payment.razorpay_order_id = order["id"]
        payment.status = "CREATED"

    db.commit()
    db.refresh(payment)

    return PaymentOrderResponse(
        payment_id=payment.id,
        service_request_id=payment.service_request_id,
        razorpay_order_id=payment.razorpay_order_id,
        razorpay_key_id=settings.razorpay_key_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
    )

@router.post(
    "/verify",
    response_model=PaymentResponse,
)
def verify_payment(
    payload: PaymentVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    payment = db.scalar(
        select(Payment).where(
            Payment.razorpay_order_id
            == payload.razorpay_order_id,
            Payment.customer_id
            == current_user.id,
        )
    )

    if payment is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment order not found",
        )

    if payment.status == "SUCCESS":

        return payment

    signature_valid = verify_payment_signature(
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )

    if not signature_valid:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature",
        )

    payment.razorpay_payment_id = (
        payload.razorpay_payment_id
    )

    payment.razorpay_signature = (
        payload.razorpay_signature
    )

    payment.status = "SUCCESS"

    payment.paid_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(payment)

    return payment

@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    payment = db.scalar(
        select(Payment).where(
            Payment.id == payment_id,
            Payment.customer_id == current_user.id,
        )
    )

    if payment is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return payment