import enum
import uuid

from geoalchemy2 import Geography

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ServiceRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ON_THE_WAY = "on_the_way"
    ARRIVED = "arrived"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ServiceRequest(Base):

    __tablename__ = "service_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    provider_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "provider_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "vehicles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "provider_services.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status: Mapped[ServiceRequestStatus] = mapped_column(
        Enum(ServiceRequestStatus),
        default=ServiceRequestStatus.PENDING,
        nullable=False,
        index=True,
    )

    problem_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    customer_address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    customer_location = mapped_column(
        Geography(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True,
        ),
        nullable=False,
    )

    estimated_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    final_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    provider_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    accepted_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer = relationship(
        "User",
        foreign_keys=[customer_id],
    )

    provider = relationship(
        "ProviderProfile",
        foreign_keys=[provider_id],
    )

    vehicle = relationship(
        "Vehicle",
        foreign_keys=[vehicle_id],
    )

    service = relationship(
        "ProviderService",
        foreign_keys=[service_id],
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )