
from fastapi import APIRouter

from . import routers

router = APIRouter(prefix="/v1")

for r in routers.list_of_routers:
    router.include_router(r)