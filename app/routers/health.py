from sqlalchemy import text
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from app.core.database import SessionLocal
from app.core.redis import check_redis_connection

router = APIRouter(
    prefix="/api/v1/system",
    tags=["System"],
)

@router.get("/system")
async def system_health():

    database_status = "healthy"

    db = SessionLocal()

    try:

        db.execute(text("SELECT 1"))

    except Exception:

        database_status = "unhealthy"

    finally:

        db.close()

    redis_status = await check_redis_connection()

    return {
        "api": "healthy",
        "database": database_status,
        "redis": (
            "healthy"
            if redis_status
            else "unhealthy"
        ),
    }