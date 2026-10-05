import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)


router = APIRouter(
    prefix="/api/v1/customer/vehicles",
    tags=["Customer Vehicles"],
)


customer_required = require_role(
    UserRole.CUSTOMER
)


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle(
    data: VehicleCreate,
    current_user: User = Depends(customer_required),
    db: Session = Depends(get_db),
):

    registration_number = (
        data.registration_number.upper().strip()
    )

    existing_vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.registration_number
            == registration_number
        )
    )

    if existing_vehicle:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle registration number already exists",
        )

    vehicle = Vehicle(
        customer_id=current_user.id,
        vehicle_type=data.vehicle_type,
        brand=data.brand,
        model=data.model,
        registration_number=registration_number,
        year=data.year,
        fuel_type=data.fuel_type,
        color=data.color,
    )

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return vehicle


@router.get(
    "",
    response_model=list[VehicleResponse],
)
def get_my_vehicles(
    current_user: User = Depends(customer_required),
    db: Session = Depends(get_db),
):

    vehicles = db.scalars(
        select(Vehicle)
        .where(
            Vehicle.customer_id == current_user.id
        )
        .order_by(Vehicle.created_at.desc())
    ).all()

    return vehicles


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
)
def get_vehicle(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(customer_required),
    db: Session = Depends(get_db),
):

    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.customer_id == current_user.id,
        )
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    return vehicle


@router.put(
    "/{vehicle_id}",
    response_model=VehicleResponse,
)
def update_vehicle(
    vehicle_id: uuid.UUID,
    data: VehicleUpdate,
    current_user: User = Depends(customer_required),
    db: Session = Depends(get_db),
):

    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.customer_id == current_user.id,
        )
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    if "registration_number" in update_data:

        registration_number = (
            update_data["registration_number"]
            .upper()
            .strip()
        )

        existing_vehicle = db.scalar(
            select(Vehicle).where(
                Vehicle.registration_number
                == registration_number,
                Vehicle.id != vehicle_id,
            )
        )

        if existing_vehicle:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vehicle registration number already exists",
            )

        update_data[
            "registration_number"
        ] = registration_number

    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)

    return vehicle


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_vehicle(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(customer_required),
    db: Session = Depends(get_db),
):

    vehicle = db.scalar(
        select(Vehicle).where(
            Vehicle.id == vehicle_id,
            Vehicle.customer_id == current_user.id,
        )
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    db.delete(vehicle)
    db.commit()

    return None