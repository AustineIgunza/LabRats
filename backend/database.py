from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="user", index=True)  # "manager" or "user"
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    
    # Add indexes for common queries
    __table_args__ = (
        Index('idx_email_active', 'email', 'is_active'),
        Index('idx_role_active', 'role', 'is_active'),
        Index('idx_username_active', 'username', 'is_active'),
    )

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    ip_address = Column(String, index=True)
    success = Column(Boolean, index=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user_agent = Column(String)
    
    # Index for security monitoring
    __table_args__ = (
        Index('idx_email_time', 'email', 'attempted_at'),
        Index('idx_ip_time', 'ip_address', 'attempted_at'),
        Index('idx_success_time', 'success', 'attempted_at'),
    )

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)
