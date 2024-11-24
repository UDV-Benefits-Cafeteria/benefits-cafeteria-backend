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
router.include_router(routers.benefits)
router.include_router(routers.categories)
router.include_router(routers.legal_entities)
router.include_router(routers.positions)
router.include_router(routers.benefit_requests)
router.include_router(routers.users)
