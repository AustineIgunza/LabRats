#!/usr/bin/env python3
"""
Simplified database setup script for LabRats application.
"""

import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
from dotenv import load_dotenv
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./labrats.db")

# Initialize SQLAlchemy
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="user", index=True)
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

def setup_database():
    """Set up the database with tables and initial data"""
    print("🔧 Setting up LabRats database...")
    
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create all tables
        print("📋 Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully")
        
        # Create session
        db = SessionLocal()
        
        try:
            # Check if manager user already exists
            existing_manager = db.query(User).filter(User.email == "admin@labrats.com").first()
            
            if not existing_manager:
                # Create initial manager user
                print("👤 Creating initial manager user...")
                
                manager_user = User(
                    email="admin@labrats.com",
                    username="admin",
                    full_name="System Administrator",
                    hashed_password=get_password_hash("admin123"),
                    role="manager",
                    is_active=True
                )
                
                db.add(manager_user)
                db.commit()
                
                print("✓ Manager user created successfully")
                print("📧 Email: admin@labrats.com")
                print("🔑 Password: admin123")
                print("⚠️  Please change the password after first login!")
            else:
                print("✓ Manager user already exists")
            
            # Create sample regular users
            sample_users = [
                {
                    "email": "user@labrats.com",
                    "username": "user1", 
                    "full_name": "Sample User",
                    "password": "user123"
                },
                {
                    "email": "john.doe@labrats.com",
                    "username": "johndoe",
                    "full_name": "John Doe", 
                    "password": "user123"
                },
                {
                    "email": "jane.smith@labrats.com",
                    "username": "janesmith",
                    "full_name": "Jane Smith",
                    "password": "user123"
                }
            ]
            
            for user_data in sample_users:
                existing_user = db.query(User).filter(User.email == user_data["email"]).first()
                
                if not existing_user:
                    print(f"👤 Creating user: {user_data['email']}")
                    
                    sample_user = User(
                        email=user_data["email"],
                        username=user_data["username"],
                        full_name=user_data["full_name"],
                        hashed_password=get_password_hash(user_data["password"]),
                        role="user",
                        is_active=True
                    )
                    
                    db.add(sample_user)
            
            db.commit()
            print("✓ Sample users created successfully")
                
        finally:
            db.close()
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📊 Database Information:")
        print(f"   URL: {DATABASE_URL}")
        print("\n🔐 Default Login Credentials:")
        print("   Manager: admin@labrats.com / admin123")
        print("   User: user@labrats.com / user123")
        print("\n🚀 You can now start the application with:")
        print("   cd c:\\Users\\mmatt\\LabRats")
        print("   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        print(f"   Make sure PostgreSQL is running and the database URL is correct")
        print(f"   Current URL: {DATABASE_URL}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
