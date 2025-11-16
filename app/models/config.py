"""
Configuration model for storing system settings in database
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class SystemConfig(Base):
    """Model for storing system configuration values"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=True)
    config_type = Column(String(50), nullable=False, default="string")  # string, email, boolean, integer
    category = Column(String(50), nullable=False, default="general")  # general, email, mapping, system
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(255), nullable=True)  # Email of admin who last updated

    def __repr__(self):
        return f"<SystemConfig(key={self.config_key}, value={self.config_value})>"


class TeamMapping(Base):
    """Model for storing team leader, CHM, and vendor mappings"""
    __tablename__ = "team_mapping"

    id = Column(Integer, primary_key=True, index=True)
    team_leader_name = Column(String(255), nullable=False, index=True)
    team_leader_email = Column(String(255), nullable=False)
    chinese_head_name = Column(String(255), nullable=True)
    chinese_head_email = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    crm = Column(String(255), nullable=True)
    vendor_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<TeamMapping(leader={self.team_leader_name}, chm={self.chinese_head_name})>"
