from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func
from app.database import Base


# Create the enum type that matches the database
role_t = postgresql.ENUM(
    "super_user", "hr", "leader", "chm", "it", "admin",
    name="role_t", create_type=False
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Match existing DB column
    full_name = Column(String(120), nullable=False)  # Match existing DB length
    role = Column(role_t, nullable=False)  # Use the PostgreSQL enum type
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Note: updated_at column doesn't exist in current DB