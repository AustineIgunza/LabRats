#!/usr/bin/env python3
"""
Database setup script for LabRats application.
This script creates the database tables and initial data.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, User, create_tables
from backend.auth import AuthService

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Database configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://labrats_user:labrats_password@localhost:5432/labrats_db")

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        db_name = DATABASE_URL.split('/')[-1]
        base_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
        
        # Connect to postgres database to create our database
        engine = create_engine(base_url)
        with engine.connect() as conn:
            conn.execute(text("COMMIT"))
            
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_catalog.pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✓ Database '{db_name}' created successfully")
            else:
                print(f"✓ Database '{db_name}' already exists")
                
    except Exception as e:
        print(f"Note: Could not auto-create database: {e}")
        print("Please ensure the database exists manually")
        return True  # Continue anyway
    
    return True

def setup_database():
    """Set up the database with tables and initial data"""
    print("Setting up LabRats database...")
    
    # Create database if it doesn't exist
    if not create_database_if_not_exists():
        return False
    
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create all tables
        print("Creating database tables...")
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
                    hashed_password=AuthService.get_password_hash("admin123"),
                    role="manager",
                    is_active=True
                )
                
                db.add(manager_user)
                db.commit()
                
                print("✓ Manager user created successfully")
                print("📧 Email: admin@labrats.com")
                print("🔑 Password: admin123")
                print("WARNING: Please change the password after first login!")
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
                        hashed_password=AuthService.get_password_hash(user_data["password"]),
                        role="user",
                        is_active=True
                    )
                    
                    db.add(sample_user)
            
            db.commit()
            print("✓ Sample users created successfully")
                
        finally:
            db.close()
        
        print("\nDatabase setup completed successfully!")
        print("\nDatabase Information:")
        print(f"   URL: {DATABASE_URL}")
        print("\nDefault Login Credentials:")
        print("   Manager: admin@labrats.com / admin123")
        print("   User: user@labrats.com / user123")
        print("\nYou can now start the application with:")
        print("   cd c:\\Users\\mmatt\\LabRats")
        print("   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
