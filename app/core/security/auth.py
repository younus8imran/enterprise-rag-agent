from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import HTTPException, Header, Depends
from datetime import datetime, timedelta

class UserIdentity(BaseModel):
    user_id: str
    username: str
    role: str # "admin", "manager", "employee"
    permissions: list[str] = Field(default_factory=list)
    tenant_id: str
    access_level: int = 1 # 1: Basic, 2: Confidential, 3: Top Secret

class AuthContext:
    """Simple context for user identity and session"""
    def __init__(self, identity: UserIdentity):
        self.identity = identity

async def get_current_user(authorization: Optional[str] = Header(None)) -> AuthContext:
    """
    Authentication middleware.
    In production, this would validate a JWT token.
    For now, it simulates identity based on a simple 'Bearer <role>' token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authentication token")

    token = authorization.split(" ")[1]

    # Mock user database
    users = {
        "admin": UserIdentity(user_id="u1", username="admin", role="admin", permissions=["*"], tenant_id="t1", access_level=3),
        "manager": UserIdentity(user_id="u2", username="manager", role="manager", permissions=["read_internal"], tenant_id="t1", access_level=2),
        "employee": UserIdentity(user_id="u3", username="employee", role="employee", permissions=["read_basic"], tenant_id="t1", access_level=1),
    }

    if token not in users:
        raise HTTPException(status_code=403, detail="Invalid user role")

    return AuthContext(identity=users[token])
