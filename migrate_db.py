#!/usr/bin/env python3
"""
Database migration script to add phone verification features
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db

def migrate_database():
    with app.app_context():
        # Add new columns to existing User table
        try:
            db.engine.execute('ALTER TABLE user ADD COLUMN phone_number VARCHAR(15)')
            print('✓ Added phone_number column to user table')
        except Exception as e:
            print(f'phone_number column may already exist: {e}')

        try:
            db.engine.execute('ALTER TABLE user ADD COLUMN city VARCHAR(100)')
            print('✓ Added city column to user table')
        except Exception as e:
            print(f'city column may already exist: {e}')

        try:
            db.engine.execute('ALTER TABLE user ADD COLUMN is_verified BOOLEAN DEFAULT 0')
            print('✓ Added is_verified column to user table')
        except Exception as e:
            print(f'is_verified column may already exist: {e}')

        # Create OTP verification table
        try:
            db.engine.execute('''
                CREATE TABLE IF NOT EXISTS otp_verification (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number VARCHAR(15) NOT NULL,
                    otp_code VARCHAR(6) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    is_used BOOLEAN DEFAULT 0
                )
            ''')
            print('✓ Created otp_verification table')
        except Exception as e:
            print(f'Error creating otp_verification table: {e}')

        print('Database migration completed!')

if __name__ == '__main__':
    migrate_database()