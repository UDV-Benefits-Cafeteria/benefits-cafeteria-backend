import random

from fastapi import APIRouter, Response

from src.api.v1.fake.generators import generate_fake_user
from src.schemas.user import (
    UserError,
    UserLogin,
    UserRegister,
    UserVerified,
    UserVerify,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signin")
async def signin(user_login: UserLogin, response: Response):
    response.set_cookie(
        key="access_token",
        value="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicm9sZSI6ImhyIiwiaWF0IjoxNTE2MjM5MDIyfQ.Zj68PKfLCbb43wfkEfYhVGPFJiQSPMdNjJnNqyWO_ts",
    )
    return {"is_success": True}


@router.post("/signup")
async def signup(user_register: UserRegister):
    generate_fake_user(user_id=user_register.id, is_verified=True)
    return {"is_success": True}


@router.post("/verify", response_model=UserVerified | UserError)
async def verify_email(email_data: UserVerify):
    email = email_data.email
    user_exists = random.choice([True, False])
    if user_exists:
        user = generate_fake_user(email=email, is_verified=False)
        return UserVerified(id=user.id)
    else:
        return UserError(error="User not found")
