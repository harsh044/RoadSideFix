from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/api/v1/customer",
    tags=["Customer"],
)


@router.get("/dashboard")
def customer_dashboard(
    current_user: User = Depends(
        require_role(UserRole.CUSTOMER)
    ),
):

    return {
        "message": "Welcome to customer dashboard",
        "user_id": str(current_user.id),
        "name": current_user.name,
        "role": current_user.role.value,
    }