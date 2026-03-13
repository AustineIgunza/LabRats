from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..database import get_db, User, LoginAttempt
from ..models import UsersListResponse, UserResponse, LoginAttemptResponse, MessageResponse, UserUpdate
from ..auth import get_manager_user
from ..rate_limiter import api_rate_limit

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/users", response_model=UsersListResponse)
@api_rate_limit
async def get_all_users(
    page: int = 1,
    per_page: int = 10,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: UserResponse = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Get all users (manager only)"""
    # Build query
    query = db.query(User)

    # Apply filters
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    users = query.order_by(User.created_at.desc()).offset(offset).limit(per_page).all()

    return UsersListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=page,
        per_page=per_page
    )


@router.put("/users/{user_id}", response_model=UserResponse)
@api_rate_limit
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Update any user (manager only)"""
    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)

    # Clear user cache
    from ..auth import AuthService
    AuthService.clear_user_cache(db_user.id)

    return db_user


@router.delete("/users/{user_id}", response_model=MessageResponse)
@api_rate_limit
async def delete_user(
    user_id: int,
    current_user: UserResponse = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Delete a user (manager only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )

    db_user = db.query(User).filter(User.id == user_id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()

    # Clear user cache
    from ..auth import AuthService
    AuthService.clear_user_cache(user_id)

    return MessageResponse(message="User deleted successfully")


@router.get("/login-attempts", response_model=List[LoginAttemptResponse])
@api_rate_limit
async def get_login_attempts(
    page: int = 1,
    per_page: int = 50,
    email: Optional[str] = None,
    success: Optional[bool] = None,
    hours: Optional[int] = 24,
    current_user: UserResponse = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    """Get login attempts for security monitoring (manager only)"""
    # Build query
    query = db.query(LoginAttempt)

    # Filter by time
    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(LoginAttempt.attempted_at >= since)

    # Apply filters
    if email:
        query = query.filter(LoginAttempt.email.ilike(f"%{email}%"))
    if success is not None:
        query = query.filter(LoginAttempt.success == success)

    # Apply pagination and ordering
    offset = (page - 1) * per_page
    attempts = query.order_by(LoginAttempt.attempted_at.desc()).offset(offset).limit(per_page).all()

    return [LoginAttemptResponse.from_orm(attempt) for attempt in attempts]
