"""Database module - re-export from main database module for backward compatibility"""
# Re-export everything from the main database module
from app.database import engine, Base, SessionLocal, get_db