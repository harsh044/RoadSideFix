# app/routers/payment_webhook.py

import hmac
import hashlib

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

from app.models.payment import Payment


router = APIRouter(
    prefix="/api/v1/webhooks",
    tags=["Payment Webhooks"],
)


def verify_webhook_signature(
    body: bytes,
    signature: str,
) -> bool:

    expected_signature = hmac.new(
        settings.razorpay_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(...),
    db: Session = Depends(get_db),
):

    body = await request.body()

    if not verify_webhook_signature(
        body=body,
        signature=x_razorpay_signature,
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    payload = await request.json()

    event = payload.get("event")

    if event == "payment.captured":

        payment_entity = (
            payload
            .get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        razorpay_payment_id = payment_entity.get(
            "id"
        )

        razorpay_order_id = payment_entity.get(
            "order_id"
        )

        if razorpay_payment_id and razorpay_order_id:

            payment = db.scalar(
                select(Payment).where(
                    Payment.razorpay_order_id
                    == razorpay_order_id
                )
            )

            if payment:

                payment.razorpay_payment_id = (
                    razorpay_payment_id
                )

                payment.status = "SUCCESS"

                db.commit()

    elif event == "payment.failed":

        payment_entity = (
            payload
            .get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        razorpay_order_id = payment_entity.get(
            "order_id"
        )

        if razorpay_order_id:

            payment = db.scalar(
                select(Payment).where(
                    Payment.razorpay_order_id
                    == razorpay_order_id
                )
            )

            if payment and payment.status != "SUCCESS":

                payment.status = "FAILED"

                db.commit()

    return {
        "status": "received"
    }