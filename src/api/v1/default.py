from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def index():
    return {"index": True}


@router.get("/ping")
async def ping():
    return {"success": True}
