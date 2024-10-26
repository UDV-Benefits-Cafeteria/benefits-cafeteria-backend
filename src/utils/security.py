from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import EmailStr

from src.config import get_settings, logger

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_reset_password_token(email: EmailStr) -> str:
    data = {"sub": email, "exp": datetime.now(UTC) + timedelta(minutes=10)}
    token = jwt.encode(data, str(settings.SECRET_KEY), "HS256")
    return token


def decode_reset_password_token(token: str) -> EmailStr | None:
    try:
        payload = jwt.decode(token, str(settings.SECRET_KEY), algorithms="HS256")
        email: EmailStr = payload.get("sub")
        return email
    except JWTError as e:
        logger.error(f"Error while decoding token: {e}")
        return None
