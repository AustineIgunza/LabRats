from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_
from cachetools import TTLCache
import json
import os
from dotenv import load_dotenv

from .database import get_db, User, LoginAttempt
from .models import UserInDB

load_dotenv()

# Security configurations
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", 15))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory cache for user sessions (TTL: 30 minutes, max 1000 entries)
user_cache = TTLCache(maxsize=1000, ttl=1800)  # 30 minutes TTL

# HTTP Bearer token scheme
security = HTTPBearer()

class AuthService:
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return {"username": username, "role": payload.get("role")}
        except JWTError:
            return None
    
    @staticmethod
    def check_account_lockout(email: str, db: Session) -> bool:
        """Check if account is locked due to failed attempts"""
        user = db.query(User).filter(User.email == email).first()
        if user and user.locked_until:
            if user.locked_until > datetime.utcnow():
                return True
            else:
                # Unlock account if lockout period has expired
                user.locked_until = None
                user.failed_login_attempts = 0
                db.commit()
        return False
    
    @staticmethod
    def record_login_attempt(email: str, ip_address: str, user_agent: str, success: bool, db: Session):
        """Record login attempt for security monitoring"""
        login_attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            success=success,
            user_agent=user_agent
        )
        db.add(login_attempt)
        db.commit()
    
    @staticmethod
    def handle_failed_login(email: str, db: Session):
        """Handle failed login attempt - increment counter and lock if needed"""
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            db.commit()
    
    @staticmethod
    def reset_failed_attempts(email: str, db: Session):
        """Reset failed login attempts after successful login"""
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
        """Authenticate user with email and password"""
        # Check if account is locked
        if AuthService.check_account_lockout(email, db):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked due to too many failed attempts. Try again later."
            )
        
        user = db.query(User).filter(
            and_(User.email == email, User.is_active == True)
        ).first()
        
        if not user or not AuthService.verify_password(password, user.hashed_password):
            if user:
                AuthService.handle_failed_login(email, db)
            return None
        
        # Reset failed attempts on successful login
        AuthService.reset_failed_attempts(email, db)
        return user
    
    @staticmethod
    def cache_user_session(user_id: int, user_data: dict):
        """Cache user session data in memory"""
        cache_key = f"user_session:{user_id}"
        user_cache[cache_key] = user_data
    
    @staticmethod
    def get_cached_user_session(user_id: int) -> Optional[dict]:
        """Get cached user session data"""
        cache_key = f"user_session:{user_id}"
        return user_cache.get(cache_key)
    
    @staticmethod
    def clear_user_cache(user_id: int):
        """Clear user session cache"""
        cache_key = f"user_session:{user_id}"
        if cache_key in user_cache:
            del user_cache[cache_key]

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserInDB:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = AuthService.verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
        
        username = token_data.get("username")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    # Try to get user from cache first
    user_cache_data = AuthService.get_cached_user_session(user.id)
    if user_cache_data:
        return UserInDB(**user_cache_data)
    
    # Cache user data
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "hashed_password": user.hashed_password
    }
    AuthService.cache_user_session(user.id, user_data)
    
    return UserInDB(**user_data)

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_manager_user(current_user: UserInDB = Depends(get_current_active_user)):
    """Require manager role"""
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Manager role required."
        )
    return current_user
