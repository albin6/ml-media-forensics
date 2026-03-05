import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class EvidenceResponse(BaseModel):
    id:          uuid.UUID
    filename:    str
    file_size:   int
    mime_type:   str
    sha256_hash: str
    media_type:  str
    status:      str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class AnalysisResultResponse(BaseModel):
    id:                uuid.UUID
    evidence_id:       uuid.UUID
    is_tampered:       Optional[bool]
    confidence_score:  Optional[float]
    processing_time_s: Optional[float]
    ela_heatmap_key:   Optional[str]
    frame_results:     Optional[list]
    created_at:        datetime

    class Config:
        from_attributes = True

class AnalysisTriggerRequest(BaseModel):
    model_version_tag: Optional[str] = None
