#!/usr/bin/env python3
"""Apply schema upgrades for the current database without deleting existing data."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import app
from app.utils.schema_migration import ensure_database_schema


def migrate_database():
    with app.app_context():
        ensure_database_schema()
        print("Database migration completed!")


if __name__ == "__main__":
    migrate_database()