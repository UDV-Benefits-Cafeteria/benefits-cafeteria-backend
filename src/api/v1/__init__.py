from fastapi import APIRouter

from . import routers

router = APIRouter(prefix="/v1")

router.include_router(routers.auth)
router.include_router(routers.benefit)
router.include_router(routers.category)
router.include_router(routers.legal_entity)
router.include_router(routers.position)
router.include_router(routers.request)
router.include_router(routers.users)
