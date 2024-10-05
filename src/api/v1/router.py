from fastapi import APIRouter

from src.api.v1 import default
from src.api.v1.fake import benefit
from src.api.v1.fake import request

router = APIRouter()
router.include_router(
    default.router,
    tags=["default"],
    prefix="/test",
)

router.include_router(benefit.router, tags=["fake"])
router.include_router(request.router, tags=["fake"])
