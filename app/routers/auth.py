import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


def find_existing_user(
    db: Session,
    phone: str,
    email: str | None,
):
    conditions = [
        User.phone == phone,
    ]

    if email:
        conditions.append(User.email == email)

    query = select(User).where(or_(*conditions))

    return db.scalar(query)


def create_user(
    db: Session,
    data: SignupRequest,
    role: UserRole,
):

    existing_user = find_existing_user(
        db,
        data.phone,
        data.email,
    )

    if existing_user:
        if existing_user.phone == data.phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already registered",
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        id=uuid.uuid4(),
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/customer/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def customer_signup(
    data: SignupRequest,
    db: Session = Depends(get_db),
):

    return create_user(
        db=db,
        data=data,
        role=UserRole.CUSTOMER,
    )


@router.post(
    "/provider/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def provider_signup(
    data: SignupRequest,
    db: Session = Depends(get_db),
):

    return create_user(
        db=db,
        data=data,
        role=UserRole.SERVICE_PROVIDER,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    query = select(User).where(
        User.phone == data.phone
    )

    user = db.scalar(query)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
    )

    refresh_token = create_refresh_token(
        user_id=str(user.id),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(
    data: RefreshRequest,
    db: Session = Depends(get_db),
):

    try:
        payload = decode_token(
            data.refresh_token
        )

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("Missing user ID")

        user = db.get(
            User,
            uuid.UUID(user_id),
        )

    except (ValueError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
    )

    new_refresh_token = create_refresh_token(
        user_id=str(user.id),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):

    return current_user