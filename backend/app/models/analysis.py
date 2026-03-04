import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, ForeignKey, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name      = Column(String(100), nullable=False)
    version_tag     = Column(String(50), nullable=False)
    architecture    = Column(String(100), nullable=False)
    dataset_trained = Column(String(200))
    accuracy        = Column(Float)
    f1_score        = Column(Float)
    sha256_checksum = Column(String(64))
    is_active       = Column(Boolean, nullable=False, default=True)
    registered_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    analysis_results = relationship("AnalysisResult", back_populates="model_version")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id       = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False)
    model_version_id  = Column(UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False)
    celery_task_id    = Column(String(255))
    is_tampered       = Column(Boolean)
    confidence_score  = Column(Float)
    processing_time_s = Column(Float)
    ela_heatmap_key   = Column(String(512))   # MinIO object key
    frame_results     = Column(JSONB)          # [{frame_no, is_tampered, confidence}]
    metadata          = Column(JSONB)
    created_at        = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    evidence      = relationship("Evidence",      back_populates="analysis_results")
    model_version = relationship("ModelVersion",  back_populates="analysis_results")
