from sqlalchemy import Column, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    res_id = Column(Integer, ForeignKey("submissions.id"), unique=True, nullable=False)  # Database column name

    # Asset Items
    laptop = Column(Boolean, default=False)
    mouse = Column(Boolean, default=False)
    headphones = Column(Boolean, default=False)
    others = Column(Text, nullable=True)

    # Overall Approval
    approved = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    submission = relationship("Submission", back_populates="assets")