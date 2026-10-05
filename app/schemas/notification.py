from datetime import datetime

from uuid import UUID

from pydantic import BaseModel


class NotificationResponse(BaseModel):

    id: UUID

    user_id: UUID

    title: str

    message: str

    notification_type: str

    is_read: bool

    created_at: datetime