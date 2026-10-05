# app/schemas/payment.py

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):

    service_request_id: UUID


class PaymentOrderResponse(BaseModel):

    payment_id: UUID

    service_request_id: UUID

    razorpay_order_id: str

    razorpay_key_id: str

    amount: Decimal

    currency: str

    status: str


class PaymentVerify(BaseModel):

    razorpay_order_id: str = Field(
        ...,
        min_length=5,
        max_length=100,
    )

    razorpay_payment_id: str = Field(
        ...,
        min_length=5,
        max_length=100,
    )

    razorpay_signature: str = Field(
        ...,
        min_length=5,
        max_length=255,
    )


class PaymentResponse(BaseModel):

    id: UUID

    service_request_id: UUID

    customer_id: UUID

    amount: Decimal

    currency: str

    status: str

    razorpay_order_id: str | None

    razorpay_payment_id: str | None

    paid_at: datetime | None