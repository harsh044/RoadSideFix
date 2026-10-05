from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.auth import (
    get_current_user,
)

from app.models.notification import (
    Notification,
)

from app.models.user import User

from app.schemas.notification import (
    NotificationResponse,
)


router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"],
)


# =========================================================
# GET ALL NOTIFICATIONS
# =========================================================

@router.get(
    "",
    response_model=list[
        NotificationResponse
    ],
)
def get_notifications(

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    notifications = db.scalars(

        select(Notification)

        .where(
            Notification.user_id
            == current_user.id
        )

        .order_by(
            Notification.created_at.desc()
        )

    ).all()

    return notifications


# =========================================================
# GET UNREAD NOTIFICATIONS
# =========================================================

@router.get(
    "/unread",
    response_model=list[
        NotificationResponse
    ],
)
def get_unread_notifications(

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    notifications = db.scalars(

        select(Notification)

        .where(
            Notification.user_id
            == current_user.id,

            Notification.is_read.is_(False),
        )

        .order_by(
            Notification.created_at.desc()
        )

    ).all()

    return notifications


# =========================================================
# MARK ONE READ
# =========================================================

@router.patch(
    "/{notification_id}/read"
)
def mark_notification_read(

    notification_id: UUID,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    notification = db.scalar(

        select(Notification)

        .where(

            Notification.id
            == notification_id,

            Notification.user_id
            == current_user.id,

        )
    )

    if not notification:

        raise HTTPException(

            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail="Notification not found",
        )

    notification.is_read = True

    db.commit()

    return {
        "message": (
            "Notification marked as read"
        )
    }


# =========================================================
# MARK ALL READ
# =========================================================

@router.patch(
    "/read-all"
)
def mark_all_notifications_read(

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    notifications = db.scalars(

        select(Notification)

        .where(

            Notification.user_id
            == current_user.id,

            Notification.is_read.is_(False),

        )
    ).all()

    for notification in notifications:

        notification.is_read = True

    db.commit()

    return {
        "message": (
            "All notifications marked as read"
        )
    }