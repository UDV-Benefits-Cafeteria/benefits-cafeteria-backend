from fastapi import APIRouter

from src.api.v1 import default

router = APIRouter()
router.include_router(default.router, tags=["default"])
