from fastapi import APIRouter

from src.api.v1 import default
from src.api.v1.fake import benefit

router = APIRouter()
router.include_router(
    default.router,
    tags=["default"],
    prefix="/test",
)
router.include_router(benefit.router, tags=["fake"])
