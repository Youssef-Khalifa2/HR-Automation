"""Database configuration and connection management"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import time
import logging
from config import settings

print(f"[DB] Initializing database connection to: {settings.DATABASE_URL}")

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pool configuration
    poolclass=QueuePool,
    pool_size=10,                    # Number of connections to maintain
    max_overflow=20,                 # Additional connections beyond pool_size
    pool_pre_ping=True,              # Validate connections before use
    pool_recycle=3600,              # Recycle connections every hour
    pool_timeout=30,                # Timeout getting connection from pool
    # Query optimization
    echo=False,                     # Set to True for SQL logging
    connect_args={
        "connect_timeout": 10,      # Connection timeout
        "options": "-c timezone=utc"  # Ensure consistent timezone
    } if "postgresql" in settings.DATABASE_URL else {}
)

# Add connection event listeners for debugging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Log when new connections are established"""
    print(f"[DB] New database connection established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log when connections are checked out from pool"""
    print(f"[DB] Connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log when connections are returned to pool"""
    print(f"[DB] Connection returned to pool")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print(f"[DB] Database session factory initialized with connection pooling")

Base = declarative_base()


def get_db():
    """Dependency to get database session with timing"""
    start_time = time.time()
    db = SessionLocal()
    connect_time = time.time() - start_time
    print(f"[DB] Database session obtained in {connect_time:.3f}s")

    try:
        yield db
    finally:
        close_start = time.time()
        db.close()
        close_time = time.time() - close_start
        print(f"[DB] Database session closed in {close_time:.3f}s")