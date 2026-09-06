from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings

security = HTTPBearer()


class TokenPayload(BaseModel):
    sub: int  # user_id as int
    username: str
    role: str
    tenant_id: int
    exp: int  # JWT stores exp as Unix timestamp


class UserIdentity(BaseModel):
    user_id: int
    username: str
    role: str
    permissions: list[str] = []
    tenant_id: int
    access_level: int = 1


class AuthContext:
    def __init__(self, identity: UserIdentity):
        self.identity = identity


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, username: str, role: str, tenant_id: int) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),  # JWT spec requires string subject
        "username": username,
        "role": role,
        "tenant_id": tenant_id,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthContext:
    """
    Validate Bearer JWT token and return AuthContext.
    Requires a valid JWT signed with JWT_SECRET.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(token)

    # Role -> permissions mapping
    role_perms = {
        "admin": ["*"],
        "manager": ["read_internal", "write_internal"],
        "employee": ["read_basic"],
    }

    identity = UserIdentity(
        user_id=int(payload.sub),  # decode back to int for DB
        username=payload.username,
        role=payload.role,
        tenant_id=payload.tenant_id,
        permissions=role_perms.get(payload.role, []),
        access_level={"admin": 3, "manager": 2, "employee": 1}.get(payload.role, 1),
    )
    return AuthContext(identity=identity)
