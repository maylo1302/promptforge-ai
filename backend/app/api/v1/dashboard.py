from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import func, select
from app.api.deps import CurrentUser, DbSession
from app.models import Prompt
from app.schemas import DashboardResponse

router = APIRouter(tags=["Panel użytkownika"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: DbSession, user: CurrentUser) -> DashboardResponse:
    base = select(Prompt).where(Prompt.user_id == user.id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    favorite = db.scalar(select(func.count()).select_from(base.where(Prompt.is_favorite.is_(True)).subquery())) or 0
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    generated = db.scalar(select(func.count()).select_from(base.where(Prompt.status == "generated", Prompt.created_at >= month_start).subquery())) or 0
    average = db.scalar(select(func.avg(Prompt.quality_score)).where(Prompt.user_id == user.id, Prompt.quality_score.is_not(None)))
    recent = list(db.scalars(base.order_by(Prompt.updated_at.desc()).limit(5)))
    return DashboardResponse(total_prompts=total, favorite_prompts=favorite, generated_this_month=generated, average_quality_score=round(float(average), 1) if average is not None else None, recent_prompts=recent)

