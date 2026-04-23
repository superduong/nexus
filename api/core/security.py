from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from api.core.config import get_settings

pwd_context = CryptContext(schemes=["django_pbkdf2_sha256"], deprecated="auto")
ALGORITHM = "HS256"


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def create_access_token(subject: dict[str, Any]) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=s.access_token_expire_minutes)
    to_encode = {**subject, "exp": expire, "token_type": "access"}
    return jwt.encode(to_encode, s.secret_key, algorithm=ALGORITHM)


def create_refresh_token(subject: dict[str, Any]) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=s.refresh_token_expire_days)
    to_encode = {**subject, "exp": expire, "token_type": "refresh"}
    return jwt.encode(to_encode, s.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    s = get_settings()
    return jwt.decode(token, s.secret_key, algorithms=[ALGORITHM])


def safe_decode_token(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except JWTError:
        return None
