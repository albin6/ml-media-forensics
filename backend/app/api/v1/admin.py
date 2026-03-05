from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.models.analysis import ModelVersion
from app.schemas.auth import UserResponse

router = APIRouter()

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 50,
):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    role: str = None,
    is_active: bool = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    if role:
        user.role = UserRole(role)
    if is_active is not None:
        user.is_active = is_active
    return user

@router.get("/audit-logs")
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 100,
):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.occurred_at.desc()).offset(skip).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "event_type": log.event_type.value,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "ip_address": str(log.ip_address) if log.ip_address else None,
            "details": log.details,
            "occurred_at": log.occurred_at.isoformat(),
        }
        for log in logs
    ]

@router.get("/models", response_model=list[dict])
async def list_models(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    result = await db.execute(select(ModelVersion))
    return [
        {
            "id": str(m.id),
            "model_name": m.model_name,
            "version_tag": m.version_tag,
            "architecture": m.architecture,
            "f1_score": m.f1_score,
            "is_active": m.is_active,
            "registered_at": m.registered_at.isoformat(),
        }
        for m in result.scalars().all()
    ]
