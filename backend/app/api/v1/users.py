from fastapi import APIRouter
from app.api.deps import CurrentUser, DbSession
from app.models import AuditLog
from app.schemas import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["Profil"])


@router.get("/me", response_model=UserResponse)
def get_me(user: CurrentUser) -> CurrentUser:
    return user


@router.patch("/me", response_model=UserResponse)
def update_me(payload: UserUpdateRequest, db: DbSession, user: CurrentUser) -> CurrentUser:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, str(value) if value is not None else None)
    db.add(AuditLog(user_id=user.id, action="profile.updated"))
    db.commit()
    db.refresh(user)
    return user

