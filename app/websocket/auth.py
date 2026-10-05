# app/websocket/auth.py

from uuid import UUID

from jose import JWTError, jwt

from app.core.config import settings


def authenticate_websocket(
    token: str | None,
) -> UUID | None:
    """
    Decode the JWT and return the authenticated user ID.

    Returns None when the token is missing or invalid.
    """

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        subject = payload.get("sub")

        if subject is None:
            return None

        return UUID(str(subject))

    except (
        JWTError,
        ValueError,
        TypeError,
    ):
        return None