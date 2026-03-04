import time
import uuid
from celery import shared_task
from celery.utils.log import get_task_logger
import httpx

from app.core.config import settings
from app.services.storage_service import StorageService

logger  = get_task_logger(__name__)
storage = StorageService()


def _get_sync_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine   = create_engine(sync_url)
    Session  = sessionmaker(bind=engine)
    return Session()


@shared_task(
    bind=True,
    name="app.tasks.video_task.run_video_analysis",
    max_retries=2,
    default_retry_delay=60,
    acks_late=True,
    time_limit=600,
    soft_time_limit=540,
)
def run_video_analysis(self, evidence_id: str, result_id: str):
    """Celery task: download video → send to ML service → persist frame results."""
    from app.models.evidence import Evidence, EvidenceStatus
    from app.models.analysis import AnalysisResult
    from app.models.audit_log import AuditLog, AuditEventType

    db = _get_sync_db()
    try:
        logger.info(f"[VideoTask] Starting for evidence={evidence_id}")
        start = time.time()

        evidence: Evidence = db.query(Evidence).filter_by(id=uuid.UUID(evidence_id)).first()
        if not evidence:
            return

        file_bytes = storage.download_bytes(settings.MINIO_EVIDENCE_BUCKET, evidence.storage_key)

        # Call ML service — video endpoint
        with httpx.Client(timeout=settings.ML_REQUEST_TIMEOUT_SECONDS) as client:
            resp = client.post(
                f"{settings.ML_SERVICE_URL}/infer/video",
                files={"file": (evidence.filename, file_bytes, evidence.mime_type)},
            )
            resp.raise_for_status()
            ml_result = resp.json()

        elapsed = time.time() - start

        # Persist analysis result
        analysis: AnalysisResult = db.query(AnalysisResult).filter_by(id=uuid.UUID(result_id)).first()
        analysis.is_tampered       = ml_result["is_tampered"]
        analysis.confidence_score  = ml_result["confidence"]
        analysis.processing_time_s = elapsed
        analysis.frame_results     = ml_result.get("frame_results", [])
        analysis.metadata          = ml_result.get("metadata", {})

        evidence.status = EvidenceStatus.completed

        db.add(AuditLog(
            user_id=evidence.uploaded_by,
            event_type=AuditEventType.analysis_complete,
            resource_id=uuid.UUID(result_id),
            details={
                "is_tampered": ml_result["is_tampered"],
                "tampered_frames": ml_result.get("tampered_frame_count", 0),
            },
        ))
        db.commit()
        logger.info(f"[VideoTask] Done for evidence={evidence_id} in {elapsed:.2f}s")

    except Exception as exc:
        db.rollback()
        logger.error(f"[VideoTask] Failed: {exc}")
        try:
            from app.models.evidence import Evidence, EvidenceStatus
            ev = db.query(Evidence).filter_by(id=uuid.UUID(evidence_id)).first()
            if ev:
                ev.status = EvidenceStatus.failed
                db.commit()
        except Exception:
            pass
        raise self.retry(exc=exc)
    finally:
        db.close()
