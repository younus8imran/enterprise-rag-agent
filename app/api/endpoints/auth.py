from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.auth import (
    AuthContext,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.models import Tenant, User
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    tenant_id: int = 1
    role: str = "employee"


class RegisterResponse(BaseModel):
    message: str
    user_id: int


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=RegisterResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check username not taken
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    # Ensure tenant exists
    tenant_res = await db.execute(select(Tenant).where(Tenant.id == req.tenant_id))
    if not tenant_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Tenant not found")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=req.role,
        tenant_id=req.tenant_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return RegisterResponse(message="User created", user_id=user.id)


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(
        user_id=str(user.id),
        username=user.username,
        role=user.role,
        tenant_id=str(user.tenant_id),
    )
    return LoginResponse(access_token=token)


@router.get("/me")
async def me(auth: AuthContext = Depends(get_current_user)):
    return {
        "user_id": auth.identity.user_id,
        "username": auth.identity.username,
        "role": auth.identity.role,
        "tenant_id": auth.identity.tenant_id,
    }
