import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, Enum, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class AuditEventType(str, enum.Enum):
    login             = "login"
    logout            = "logout"
    upload            = "upload"
    analysis_start    = "analysis_start"
    analysis_complete = "analysis_complete"
    download          = "download"
    admin_action      = "admin_action"
    auth_failure      = "auth_failure"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type  = Column(Enum(AuditEventType), nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to evidence or result
    ip_address  = Column(INET, nullable=True)
    user_agent  = Column(Text)
    details     = Column(JSONB)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
