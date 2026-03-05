from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta
from typing import List, Optional
import os
from dotenv import load_dotenv

from .database import get_db, User, LoginAttempt, create_tables
from .models import (
    UserCreate, UserResponse, UserUpdate, LoginRequest, 
    LoginResponse, MessageResponse, UsersListResponse,
    LoginAttemptResponse
)
from .auth import (
    AuthService, get_current_user, get_current_active_user, 
    get_manager_user
)
from .rate_limiter import (
    login_rate_limit, api_rate_limit, RateLimitMiddleware,
    dos_protection
)

load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="LabRats Management System",
    description="A secure user management system with role-based access control",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Mount static files (for frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Security bearer scheme
security = HTTPBearer()

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Root endpoint - serve the frontend
@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>LabRats API Server</h1><p>Frontend files not found. API documentation: <a href='/api/docs'>/api/docs</a></p>", 
            status_code=200
        )

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@api_rate_limit
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        # Record failed attempt
        AuthService.record_login_attempt(
            user_data.email,
            request.client.host if request.client else "unknown",
            request.headers.get("user-agent", ""),
            False,
            db
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    
    # Hash password
    hashed_password = AuthService.get_password_hash(user_data.password)
    
    # Create user
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role or "user"
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/api/auth/login", response_model=LoginResponse)
@login_rate_limit
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token"""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    
    try:
        # Authenticate user
        user = AuthService.authenticate_user(login_data.email, login_data.password, db)
        
        if not user:
            # Record failed attempt
            AuthService.record_login_attempt(login_data.email, client_ip, user_agent, False, db)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
        access_token = AuthService.create_access_token(
            data={"sub": user.username, "role": user.role},
            expires_delta=access_token_expires
        )
        
        # Record successful attempt
        AuthService.record_login_attempt(login_data.email, client_ip, user_agent, True, db)
        
        # Cache user session
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active
        }
        AuthService.cache_user_session(user.id, user_data)
        
        return LoginResponse(
            access_token=access_token,
            expires_in=int(access_token_expires.total_seconds()),
            user=UserResponse(**user_data)
        )
        
    except HTTPException as e:
        if e.status_code == status.HTTP_423_LOCKED:
            # Record failed attempt for locked account
            AuthService.record_login_attempt(login_data.email, client_ip, user_agent, False, db)
        raise e

@app.post("/api/auth/logout", response_model=MessageResponse)
async def logout(current_user: UserResponse = Depends(get_current_active_user)):
    """Logout user and clear session cache"""
    AuthService.clear_user_cache(current_user.id)
    return MessageResponse(message="Successfully logged out")

# User management endpoints
@app.get("/api/users/me", response_model=UserResponse)
@api_rate_limit
async def get_current_user_info(current_user: UserResponse = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user

@app.put("/api/users/me", response_model=UserResponse)
@api_rate_limit
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    db_user = db.query(User).filter(User.id == current_user.id).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    # Clear cache to force refresh
    AuthService.clear_user_cache(db_user.id)
    
    return db_user

# Manager-only endpoints
@app.get("/api/admin/users", response_model=UsersListResponse)
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

@app.put("/api/admin/users/{user_id}", response_model=UserResponse)
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
    AuthService.clear_user_cache(db_user.id)
    
    return db_user

@app.delete("/api/admin/users/{user_id}", response_model=MessageResponse)
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
    AuthService.clear_user_cache(user_id)
    
    return MessageResponse(message="User deleted successfully")

# Security monitoring endpoints
@app.get("/api/admin/login-attempts", response_model=List[LoginAttemptResponse])
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend"]
    )
