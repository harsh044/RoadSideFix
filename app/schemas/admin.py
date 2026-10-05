from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from pydantic import BaseModel, EmailStr

from pydantic import BaseModel, EmailStr


class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str


class AdminResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone: str
    role: str

    class Config:
        from_attributes = True
        
class AdminUserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str | None
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminProviderResponse(BaseModel):
    id: UUID
    user_id: UUID
    business_name: str
    description: str | None
    phone: str | None
    address: str | None

    model_config = ConfigDict(from_attributes=True)


class AdminServiceRequestResponse(BaseModel):
    id: UUID
    customer_id: UUID
    provider_id: UUID | None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminPaymentResponse(BaseModel):
    id: UUID
    service_request_id: UUID
    customer_id: UUID
    amount: Decimal
    currency: str
    status: str
    razorpay_order_id: str | None
    razorpay_payment_id: str | None
    paid_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_customers: int
    total_providers: int
    total_admins: int
    active_users: int
    inactive_users: int

    total_service_requests: int
    pending_requests: int
    accepted_requests: int
    completed_requests: int
    cancelled_requests: int

    total_payments: int
    successful_payments: int
    failed_payments: int

    total_reviews: int