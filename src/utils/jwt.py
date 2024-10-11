from datetime import datetime, timedelta, timezone

import jwt

from src.config import settings


def create_access_token(
    user_id: str,
    role: str,
    expires_delta: timedelta = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": datetime.now(timezone.utc) + expires_delta,
        "sub": user_id,
        "role": role,
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt
