from fastapi import APIRouter, Depends

from src.api.v1.dependencies import get_current_user
from src.schemas.user import UserRead

router = APIRouter(prefix="/protected", tags=["Protected"])


@router.get("/")
async def protected_route(current_user: UserRead = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.firstname}!"}
