from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.shared.config import settings

###
# Password Hash
###

pwd_hasher = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    return pwd_hasher.hash(plain_password)


def verify_password(plain_password: str, hash_password: str) -> bool:
    return pwd_hasher.verify(plain_password, hash_password)


###
# JWT
###


def create_access_token(user_uid: str, user_role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_uid,
        "exp": expire,
        "role": user_role,
        "tid": str(uuid4()),
    }

    return jwt.encode(
        payload=payload,
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token=token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )  # Token Invalid Error should caught in API level using exception
