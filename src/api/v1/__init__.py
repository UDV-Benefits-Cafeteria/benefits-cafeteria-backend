from fastapi import APIRouter
from src.config import get_settings
from . import routers
from .dependencies import BaseLimiter

settings = get_settings()

if not settings.DEBUG:
    router = APIRouter(prefix="/v1", dependencies=(BaseLimiter,))
else:
    router = APIRouter(prefix="/v1")


router.include_router(routers.auth)
router.include_router(routers.benefit)
router.include_router(routers.category)
router.include_router(routers.legal_entity)
router.include_router(routers.position)
router.include_router(routers.request)
router.include_router(routers.users)
