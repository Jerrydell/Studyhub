#!/usr/bin/env python3
"""
Database migration script for Phase 3
Adds Subject and Note tables to existing database
"""

from app import create_app
from app.extensions import db
from app.models import User, Subject, Note

def migrate_database():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        
        # Create all tables
        db.create_all()
        
        print("✓ Database migration complete!")
        print("\nTables created:")
        print("  - users")
        print("  - subjects")
        print("  - notes")
        print("\nRelationships:")
        print("  - User -> Subject (one-to-many)")
        print("  - Subject -> Note (one-to-many)")
        print("\nYou can now run the application:")
        print("  python run.py")

if __name__ == '__main__':
    migrate_database()
