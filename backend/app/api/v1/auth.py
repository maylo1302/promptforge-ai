from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from sqlalchemy import select, update
from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_password, token_fingerprint, verify_password
from app.models import AuditLog, PasswordResetToken, RefreshToken, User
from app.schemas import AuthResponse, LoginRequest, Message, PasswordChangeRequest, PasswordResetConfirm, PasswordResetRequest, RegisterRequest, UserResponse
from app.services.email import email_service

router = APIRouter(prefix="/auth", tags=["Uwierzytelnianie"])


def set_auth_cookies(response: Response, refresh_token: str, csrf_token: str) -> None:
    common = {"secure": settings.is_production, "samesite": "lax", "path": "/api/v1/auth"}
    response.set_cookie("refresh_token", refresh_token, httponly=True, max_age=settings.refresh_token_expire_days * 86400, **common)
    response.set_cookie("csrf_token", csrf_token, httponly=False, max_age=settings.refresh_token_expire_days * 86400, **common)


def issue_tokens(response: Response, db: DbSession, user: User) -> AuthResponse:
    raw_refresh, expires_at = create_refresh_token()
    csrf_token = token_urlsafe(32)
    db.add(RefreshToken(user_id=user.id, token_hash=token_fingerprint(raw_refresh), expires_at=expires_at))
    db.add(AuditLog(user_id=user.id, action="session.created"))
    db.commit()
    set_auth_cookies(response, raw_refresh, csrf_token)
    return AuthResponse(access_token=create_access_token(user.id, user.is_admin), csrf_token=csrf_token)


def enforce_csrf(request: Request, csrf_cookie: str | None) -> None:
    if not csrf_cookie or request.headers.get("X-CSRF-Token") != csrf_cookie:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nieprawidłowy token CSRF.")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> User:
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="Konto z tym adresem e-mail już istnieje.")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), first_name=payload.first_name.strip(), last_name=payload.last_name.strip())
    db.add(user)
    db.flush()
    db.add(AuditLog(user_id=user.id, action="user.registered"))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: DbSession) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nieprawidłowy e-mail lub hasło.")
    return issue_tokens(response, db, user)


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: DbSession, refresh_token: str | None = Cookie(default=None), csrf_token: str | None = Cookie(default=None)) -> AuthResponse:
    enforce_csrf(request, csrf_token)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Brak sesji do odświeżenia.")
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_fingerprint(refresh_token), RefreshToken.revoked_at.is_(None)))
    if stored is None or stored.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Sesja wygasła. Zaloguj się ponownie.")
    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Konto jest niedostępne.")
    stored.revoked_at = datetime.now(timezone.utc)
    return issue_tokens(response, db, user)


@router.post("/logout", response_model=Message)
def logout(request: Request, response: Response, db: DbSession, refresh_token: str | None = Cookie(default=None), csrf_token: str | None = Cookie(default=None)) -> Message:
    enforce_csrf(request, csrf_token)
    if refresh_token:
        db.execute(update(RefreshToken).where(RefreshToken.token_hash == token_fingerprint(refresh_token)).values(revoked_at=datetime.now(timezone.utc)))
        db.commit()
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    response.delete_cookie("csrf_token", path="/api/v1/auth")
    return Message(message="Wylogowano pomyślnie.")


@router.post("/change-password", response_model=Message)
def change_password(payload: PasswordChangeRequest, db: DbSession, user: CurrentUser) -> Message:
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Obecne hasło jest nieprawidłowe.")
    user.password_hash = hash_password(payload.new_password)
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked_at=datetime.now(timezone.utc)))
    db.add(AuditLog(user_id=user.id, action="password.changed"))
    db.commit()
    return Message(message="Hasło zostało zmienione. Zaloguj się ponownie.")


@router.post("/password-reset", response_model=Message)
def request_password_reset(payload: PasswordResetRequest, db: DbSession) -> Message:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user:
        raw_token = token_urlsafe(48)
        db.add(PasswordResetToken(user_id=user.id, token_hash=token_fingerprint(raw_token), expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)))
        db.add(AuditLog(user_id=user.id, action="password.reset_requested"))
        db.commit()
        email_service.send_password_reset(user.email, raw_token)
    return Message(message="Jeżeli konto istnieje, wysłaliśmy instrukcję odzyskania hasła.")


@router.post("/password-reset/confirm", response_model=Message)
def confirm_password_reset(payload: PasswordResetConfirm, db: DbSession) -> Message:
    record = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_fingerprint(payload.token), PasswordResetToken.used_at.is_(None)))
    if record is None or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Link do zmiany hasła jest nieważny lub wygasł.")
    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="Nie można zmienić hasła dla tego konta.")
    user.password_hash = hash_password(payload.new_password)
    record.used_at = datetime.now(timezone.utc)
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked_at=datetime.now(timezone.utc)))
    db.add(AuditLog(user_id=user.id, action="password.reset_completed"))
    db.commit()
    return Message(message="Hasło zostało zmienione. Możesz się zalogować.")
