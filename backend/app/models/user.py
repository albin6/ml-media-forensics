import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, BigInteger, Float,
    Enum, ForeignKey, Text, DateTime, Index
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

class UserRole(str, enum.Enum):
    analyst = "analyst"
    admin   = "admin"
    viewer  = "viewer"

class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(255))
    role          = Column(Enum(UserRole), nullable=False, default=UserRole.analyst)
    is_active     = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_login    = Column(DateTime(timezone=True))

    evidence   = relationship("Evidence",   back_populates="uploader")
    audit_logs = relationship("AuditLog",   back_populates="user")
