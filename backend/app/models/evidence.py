import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, BigInteger, Enum, ForeignKey,
    Boolean, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.db.base import Base

class MediaType(str, enum.Enum):
    image = "image"
    video = "video"

class EvidenceStatus(str, enum.Enum):
    pending    = "pending"
    processing = "processing"
    completed  = "completed"
    failed     = "failed"

class Evidence(Base):
    __tablename__ = "evidence"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    filename    = Column(String(255), nullable=False)
    storage_key = Column(String(512), nullable=False, unique=True)
    file_size   = Column(BigInteger, nullable=False)
    mime_type   = Column(String(100), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    media_type  = Column(Enum(MediaType), nullable=False)
    status      = Column(Enum(EvidenceStatus), nullable=False, default=EvidenceStatus.pending)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    ip_address  = Column(INET, nullable=False)
    is_deleted  = Column(Boolean, nullable=False, default=False)

    uploader         = relationship("User",           back_populates="evidence")
    analysis_results = relationship("AnalysisResult", back_populates="evidence")
