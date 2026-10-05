from uuid import UUID

from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
)


def create_notification(

    db: Session,

    user_id: UUID,

    title: str,

    message: str,

    notification_type: str,

) -> Notification:

    notification = Notification(

        user_id=user_id,

        title=title,

        message=message,

        notification_type=notification_type,

    )

    db.add(
        notification
    )

    return notification