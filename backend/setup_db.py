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

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from database import Base, User, create_tables
from auth import AuthService

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Database configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://labrats_user:labrats_password@localhost:5432/labrats_db")

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    # Extract database name from URL
    try:
        db_name = DATABASE_URL.split('/')[-1]
        base_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
        
        # Connect to postgres database to create our database
        engine = create_engine(base_url)
        with engine.connect() as conn:
            # Set autocommit mode
            conn.execute(text("COMMIT"))
            
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_catalog.pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                # Create database
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✓ Database '{db_name}' created successfully")
            else:
                print(f"✓ Database '{db_name}' already exists")
                
    except Exception as e:
        print(f"Note: Could not auto-create database: {e}")
        print("Please ensure the database exists manually or check your DATABASE_URL")
        return True  # Continue anyway
    
    return True
        
        # Create user
        print(f"Creating user '{DB_USER}'...")
        try:
            cursor.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'")
            print("User created successfully.")
        except psycopg2.errors.DuplicateObject:
            print("User already exists.")
        
        # Grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}")
        cursor.execute(f"ALTER USER {DB_USER} CREATEDB")
        print("Privileges granted.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database setup error: {e}")
        return False
    
    return True

def create_tables_and_data():
    """Create tables and insert initial data"""
    try:
        # Create database connection
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
        
        # Create initial users
        db = SessionLocal()
        
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("Creating default admin user...")
            admin_user = User(
                email="admin@labrats.com",
                username="admin",
                hashed_password=AuthService.get_password_hash("admin123"),
                full_name="System Administrator",
                role="manager",
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
        
        # Check if demo user exists
        demo_user = db.query(User).filter(User.username == "demo").first()
        if not demo_user:
            print("Creating demo user...")
            demo_user = User(
                email="demo@labrats.com",
                username="demo",
                hashed_password=AuthService.get_password_hash("demo123"),
                full_name="Demo User",
                role="user",
                created_at=datetime.utcnow()
            )
            db.add(demo_user)
        
        db.commit()
        db.close()
        
        print("Initial data created successfully.")
        print("\nDefault users:")
        print("Admin - Email: admin@labrats.com, Password: admin123")
        print("Demo  - Email: demo@labrats.com, Password: demo123")
        
    except Exception as e:
        print(f"Table/data creation error: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("=== LabRats Database Setup ===")
    print()
    
    # Step 1: Create database and user
    if not create_database():
        print("Failed to create database. Exiting.")
        return
    
    print()
    
    # Step 2: Create tables and initial data
    if not create_tables_and_data():
        print("Failed to create tables and data. Exiting.")
        return
    
    print()
    print("=== Setup Complete ===")
    print("Database setup completed successfully!")
    print("You can now start the application with: python main.py")
    print()
    print("Access the application at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/api/docs")

if __name__ == "__main__":
    main()
