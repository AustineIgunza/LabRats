from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
import os
from datetime import timedelta
from typing import Optional

from ..database import get_db, User
from ..models import UserCreate, LoginRequest, LoginResponse, UserResponse, MessageResponse
from ..auth import AuthService, get_current_active_user
from ..rate_limiter import login_rate_limit, api_rate_limit

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _get_client_ip(request: Optional[Request]) -> str:
    """Simple extraction of client IP from headers or request.client."""
    if not request:
        return "unknown"

    # Prefer X-Forwarded-For / X-Real-IP when behind proxies
    try:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real = request.headers.get("x-real-ip")
        if real:
            return real
    except Exception:
        pass

    # Fallback to request.client
    if hasattr(request, "client") and request.client:
        client = request.client
        if isinstance(client, tuple):
            return client[0]
        if hasattr(client, "host"):
            return client.host

    return "unknown"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@api_rate_limit
async def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user."""
    client_ip = _get_client_ip(request)

    try:
        # Check existing
        existing = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        if existing:
            # Record attempt (best-effort)
            try:
                AuthService.record_login_attempt(user_data.email, client_ip, request.headers.get("user-agent", ""), False, db)
            except Exception:
                pass
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already registered")

        # Create user
        hashed = AuthService.get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed,
            full_name=user_data.full_name,
            role=user_data.role or "user"
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return UserResponse.from_orm(db_user)

    except HTTPException:
        raise
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=LoginResponse)
@login_rate_limit
async def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate and return JWT token."""
    client_ip = _get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    try:
        user = AuthService.authenticate_user(login_data.email, login_data.password, db)
        if not user:
            try:
                AuthService.record_login_attempt(login_data.email, client_ip, user_agent, False, db)
            except Exception:
                pass
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

        expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
        token = AuthService.create_access_token(data={"sub": user.username, "role": user.role}, expires_delta=expires)

        try:
            AuthService.record_login_attempt(login_data.email, client_ip, user_agent, True, db)
        except Exception:
            pass

        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active
        }
        try:
            AuthService.cache_user_session(user.id, user_data)
        except Exception:
            pass

        return LoginResponse(access_token=token, expires_in=int(expires.total_seconds()), user=UserResponse(**user_data))

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: UserResponse = Depends(get_current_active_user)):
    """Clear cached session for the authenticated user."""
    try:
        AuthService.clear_user_cache(current_user.id)
    except Exception:
        pass
    return MessageResponse(message="Successfully logged out")
