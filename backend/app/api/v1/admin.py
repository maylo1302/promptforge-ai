from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from sqlalchemy import func, select
from app.api.deps import AdminUser, DbSession
from app.models import AuditLog, Prompt, User
from app.schemas import AdminStatsResponse, UserResponse

router = APIRouter(prefix="/admin", tags=["Administracja"])


@router.get("/stats", response_model=AdminStatsResponse)
def stats(db: DbSession, admin: AdminUser) -> AdminStatsResponse:
    since = datetime.now(timezone.utc) - timedelta(days=30)
    active = db.scalar(select(func.count(func.distinct(AuditLog.user_id))).where(AuditLog.created_at >= since)) or 0
    return AdminStatsResponse(users=db.scalar(select(func.count()).select_from(User)) or 0, prompts=db.scalar(select(func.count()).select_from(Prompt)) or 0, generated_prompts=db.scalar(select(func.count()).select_from(Prompt).where(Prompt.status == "generated")) or 0, active_last_30_days=active)


@router.get("/users", response_model=list[UserResponse])
def users(db: DbSession, admin: AdminUser, limit: int = Query(50, ge=1, le=100)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc()).limit(limit)))

