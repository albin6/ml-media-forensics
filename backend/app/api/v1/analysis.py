import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import require_analyst, require_admin
from app.core.config import settings
from app.db.session import get_db
from app.models.analysis import AnalysisResult, ModelVersion
from app.models.audit_log import AuditLog, AuditEventType
from app.models.evidence import Evidence, EvidenceStatus, MediaType
from app.models.user import User
from app.schemas.evidence import AnalysisResultResponse, AnalysisTriggerRequest
from app.services.storage_service import StorageService
from app.tasks.image_task import run_image_analysis
from app.tasks.video_task import run_video_analysis

router  = APIRouter()
storage = StorageService()


@router.post("/{evidence_id}", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def trigger_analysis(
    evidence_id: uuid.UUID,
    body: AnalysisTriggerRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    # Fetch evidence
    result = await db.execute(select(Evidence).where(
        Evidence.id == evidence_id, Evidence.is_deleted == False
    ))
    evidence: Evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if evidence.uploaded_by != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    if evidence.status == EvidenceStatus.processing:
        raise HTTPException(status_code=409, detail="Analysis already in progress")

    # Resolve model version
    model_query = select(ModelVersion).where(ModelVersion.is_active == True)
    if body.model_version_tag:
        model_query = model_query.where(ModelVersion.version_tag == body.model_version_tag)
    model_result = await db.execute(model_query.limit(1))
    model_version: ModelVersion = model_result.scalar_one_or_none()
    if not model_version:
        raise HTTPException(status_code=404, detail="No active model version found")

    # Create placeholder result
    analysis = AnalysisResult(
        evidence_id=evidence.id,
        model_version_id=model_version.id,
    )
    db.add(analysis)
    evidence.status = EvidenceStatus.processing
    await db.flush()

    # Dispatch Celery task
    celery_fn = run_image_analysis if evidence.media_type == MediaType.image else run_video_analysis
    task = celery_fn.apply_async(
        args=[str(evidence.id), str(analysis.id)],
        queue="image_queue" if evidence.media_type == MediaType.image else "video_queue",
    )
    analysis.celery_task_id = task.id

    # Audit
    db.add(AuditLog(
        user_id=current_user.id,
        event_type=AuditEventType.analysis_start,
        resource_id=evidence.id,
        ip_address=request.client.host,
        details={"task_id": task.id, "model_version": model_version.version_tag},
    ))
    return {"task_id": task.id, "result_id": str(analysis.id), "status": "processing"}


@router.get("/{result_id}", response_model=AnalysisResultResponse)
async def get_result(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    res = await db.execute(select(AnalysisResult).where(AnalysisResult.id == result_id))
    result = res.scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.get("/{result_id}/heatmap")
async def get_heatmap(
    result_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    res = await db.execute(select(AnalysisResult).where(AnalysisResult.id == result_id))
    result = res.scalar_one_or_none()
    if not result or not result.ela_heatmap_key:
        raise HTTPException(status_code=404, detail="Heatmap not available")
    # Generate a presigned URL (1 hour expiry)
    url = storage.presigned_url(settings.MINIO_RESULTS_BUCKET, result.ela_heatmap_key, expires=3600)
    return RedirectResponse(url=url)
