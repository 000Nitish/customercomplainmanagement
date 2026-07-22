#!/usr/bin/env python
"""Initialize database tables (alternative to alembic for quick start)."""
from app.database import engine, Base
from app import models  # noqa: F401

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")
