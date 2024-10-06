from typing import Dict

from fastapi import APIRouter
from src.schemas.user import UserRegister, UserLogin, UserVerify, UserTokens, UserVerified, UserError


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/signin")
async def signin(user: UserLogin) -> UserTokens | UserError:
    pass


async def signup(user: UserRegister) -> UserTokens | UserError:
    pass


async def verify_email(email: UserVerify) -> UserVerified | UserError:
    pass
