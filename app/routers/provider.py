from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/api/v1/provider",
    tags=["Service Provider"],
)


@router.get("/dashboard")
def provider_dashboard(
    current_user: User = Depends(
        require_role(UserRole.SERVICE_PROVIDER)
    ),
):

    return {
        "message": "Welcome to service provider dashboard",
        "user_id": str(current_user.id),
        "name": current_user.name,
        "role": current_user.role.value,
    }