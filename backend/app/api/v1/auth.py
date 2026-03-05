from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token, decode_token
)
from app.db.session import get_db
from app.models.user import User
from app.models.audit_log import AuditLog, AuditEventType
from app.schemas.auth import (
    LoginRequest, RegisterRequest,
    TokenResponse, RefreshRequest
)

router = APIRouter()

def _get_redis():
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)

async def _log_event(db: AsyncSession, event: AuditEventType, request: Request,
                     user_id=None, details: dict = None):
    log = AuditLog(
        user_id=user_id,
        event_type=event,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        details=details or {},
    )
    db.add(log)

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()

    await _log_event(db, AuditEventType.login, request, user.id, {"action": "register"})

    access_token  = create_access_token(str(user.id), user.role.value)
    refresh_token, jti = create_refresh_token(str(user.id))

    redis = _get_redis()
    await redis.setex(
        f"refresh:{jti}",
        settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        str(user.id),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    user: User = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        await _log_event(db, AuditEventType.auth_failure, request, details={"email": body.email})
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login = datetime.now(timezone.utc)
    await _log_event(db, AuditEventType.login, request, user.id)

    access_token = create_access_token(str(user.id), user.role.value)
    refresh_token, jti = create_refresh_token(str(user.id))

    redis = _get_redis()
    await redis.setex(
        f"refresh:{jti}",
        settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        str(user.id),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Not a refresh token")
        jti     = payload["jti"]
        user_id = payload["sub"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    redis = _get_redis()
    stored = await redis.get(f"refresh:{jti}")
    if not stored or stored != user_id:
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    await redis.delete(f"refresh:{jti}")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access  = create_access_token(str(user.id), user.role.value)
    new_refresh, new_jti = create_refresh_token(str(user.id))
    await redis.setex(
        f"refresh:{new_jti}",
        settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        str(user.id),
    )
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        jti = payload.get("jti")
        user_id = payload.get("sub")
        redis = _get_redis()
        await redis.delete(f"refresh:{jti}")
        await _log_event(db, AuditEventType.logout, request, user_id)
    except Exception:
        pass
