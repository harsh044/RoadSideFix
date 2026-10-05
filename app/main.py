from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
# from app.core.redis import (
#     check_redis_connection,
#     close_redis_connection,
# )

from app.core.database import Base, engine

from app.routers.auth import router as auth_router
from app.routers.customer import router as customer_router
from app.routers.health import router as health_router
from app.routers.provider import router as provider_router
from app.routers.provider_profile import (
    router as provider_profile_router,
)
from app.routers.provider_services import (
    router as provider_services_router,
)
from app.routers.vehicles import router as vehicle_router
from app.routers.provider_search import (
    router as provider_search_router,
)
from app.routers.service_requests import (
    router as service_request_router,
)
from app.routers.provider_location import (
    router as provider_location_router,
)

from app.routers.tracking import (
    router as tracking_router,
)

from app.routers.notifications import (
    router as notification_router,
)

from app.routers.payments import router as payment_router

from app.routers.payment_webhook import (
    router as payment_webhook_router,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import (
    validation_exception_handler,
)
from app.routers.reviews import router as review_router
from app.routers.admin import router as admin_router

# @asynccontextmanager
# async def lifespan(app: FastAPI):

#     # Create tables if they don't already exist
#     Base.metadata.create_all(bind=engine)

#     """
#     Application startup and shutdown lifecycle.
#     """

#     redis_available = await check_redis_connection()

#     if redis_available:
#         print("Redis connection successful")
#     else:
#         print("WARNING: Redis connection failed")

#     yield

#     await close_redis_connection()
#     print("Redis connection closed")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Mobile vehicle repair service API",
    # lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://road-side-fix.vercel.app/"
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(customer_router)
app.include_router(provider_router)
app.include_router(vehicle_router)
app.include_router(provider_profile_router)
app.include_router(provider_services_router)
app.include_router(provider_search_router)
app.include_router(service_request_router)
app.include_router(provider_location_router)
app.include_router(tracking_router)
app.include_router(notification_router)
app.include_router(payment_router)
app.include_router(payment_webhook_router)
app.include_router(review_router)
app.include_router(admin_router)

@app.get("/")
def root():
    return {
        "message": "Vehicle Repair API",
        "version": "1.0.0",
    }
