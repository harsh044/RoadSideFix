# app/services/razorpay_service.py

import razorpay

from app.core.config import settings


client = razorpay.Client(
    auth=(
        settings.razorpay_key_id,
        settings.razorpay_key_secret,
    )
)


def create_razorpay_order(
    amount_in_rupees: int,
    receipt: str,
):

    amount_in_paise = amount_in_rupees * 100

    order_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1,
    }

    return client.order.create(
        data=order_data
    )


def verify_payment_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> bool:

    try:

        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        )

        return True

    except razorpay.errors.SignatureVerificationError:

        return False