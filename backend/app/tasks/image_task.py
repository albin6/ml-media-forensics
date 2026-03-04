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
    """Synchronous DB session for Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    engine   = create_engine(sync_url)
    Session  = sessionmaker(bind=engine)
    return Session()


@shared_task(
    bind=True,
    name="app.tasks.image_task.run_image_analysis",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def run_image_analysis(self, evidence_id: str, result_id: str):
    """Celery task: download image → send to ML service → persist result."""
    from app.models.evidence import Evidence, EvidenceStatus
    from app.models.analysis import AnalysisResult
    from app.models.audit_log import AuditLog, AuditEventType

    db = _get_sync_db()
    try:
        logger.info(f"[ImageTask] Starting for evidence={evidence_id}")
        start = time.time()

        # Download file from MinIO
        evidence: Evidence = db.query(Evidence).filter_by(id=uuid.UUID(evidence_id)).first()
        if not evidence:
            logger.error(f"[ImageTask] Evidence not found: {evidence_id}")
            return

        file_bytes = storage.download_bytes(settings.MINIO_EVIDENCE_BUCKET, evidence.storage_key)

        # Call ML service
        with httpx.Client(timeout=settings.ML_REQUEST_TIMEOUT_SECONDS) as client:
            resp = client.post(
                f"{settings.ML_SERVICE_URL}/infer/image",
                files={"file": (evidence.filename, file_bytes, evidence.mime_type)},
            )
            resp.raise_for_status()
            ml_result = resp.json()

        elapsed = time.time() - start

        # Persist heatmap to MinIO
        heatmap_key = None
        if ml_result.get("ela_heatmap_bytes"):
            import base64
            heatmap_bytes = base64.b64decode(ml_result["ela_heatmap_bytes"])
            heatmap_key   = f"results/{result_id}/ela_heatmap.png"
            storage.upload_bytes(settings.MINIO_RESULTS_BUCKET, heatmap_key, heatmap_bytes, "image/png")

        # Update DB
        analysis: AnalysisResult = db.query(AnalysisResult).filter_by(id=uuid.UUID(result_id)).first()
        analysis.is_tampered       = ml_result["is_tampered"]
        analysis.confidence_score  = ml_result["confidence"]
        analysis.processing_time_s = elapsed
        analysis.ela_heatmap_key   = heatmap_key
        analysis.metadata          = ml_result.get("metadata", {})

        evidence.status = EvidenceStatus.completed

        db.add(AuditLog(
            user_id=evidence.uploaded_by,
            event_type=AuditEventType.analysis_complete,
            resource_id=uuid.UUID(result_id),
            details={"is_tampered": ml_result["is_tampered"], "confidence": ml_result["confidence"]},
        ))
        db.commit()
        logger.info(f"[ImageTask] Done for evidence={evidence_id} in {elapsed:.2f}s")

    except Exception as exc:
        db.rollback()
        logger.error(f"[ImageTask] Failed: {exc}")
        # Mark evidence as failed
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
