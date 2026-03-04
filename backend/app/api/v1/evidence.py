import io
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import magic

from app.api.dependencies import require_analyst, require_admin
from app.core.config import settings
from app.core.logging import logger
from app.core.security import compute_sha256
from app.db.session import get_db
from app.models.evidence import Evidence, MediaType, EvidenceStatus
from app.models.audit_log import AuditLog, AuditEventType
from app.models.user import User
from app.schemas.evidence import EvidenceResponse
from app.services.storage_service import StorageService

router = APIRouter()
storage = StorageService()

IMAGE_TYPES = set(settings.ALLOWED_IMAGE_TYPES.split(","))
VIDEO_TYPES = set(settings.ALLOWED_VIDEO_TYPES.split(","))


def _detect_media_type(mime: str) -> MediaType:
    if mime in IMAGE_TYPES:
        return MediaType.image
    if mime in VIDEO_TYPES:
        return MediaType.video
    raise HTTPException(status_code=415, detail=f"Unsupported media type: {mime}")


@router.post("/upload", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    # ── Read file bytes ───────────────────────────────────────────────────────
    file_bytes: bytes = bytes(await file.read())
    file_size  = len(file_bytes)

    # ── MIME validation via libmagic (not just Content-Type header) ───────────
    header_sample: bytes = file_bytes[:2048]  # type: ignore[index]  # Pyre2 bug: bytes IS sliceable
    detected_mime = magic.from_buffer(header_sample, mime=True)
    if detected_mime not in settings.allowed_mime_types:
        raise HTTPException(status_code=415, detail=f"File type not permitted: {detected_mime}")

    media_type = _detect_media_type(detected_mime)

    # ── Size limits ───────────────────────────────────────────────────────────
    max_size = settings.max_image_bytes if media_type == MediaType.image else settings.max_video_bytes
    if file_size > max_size:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size")

    # ── Forensic SHA-256 hash ─────────────────────────────────────────────────
    sha256 = compute_sha256(file_bytes)
    logger.info("evidence_upload", user_id=str(current_user.id), sha256=sha256, size=file_size)

    # ── UUID-based storage key (never derived from original filename) ─────────
    storage_key = f"evidence/{uuid.uuid4()}/{uuid.uuid4()}.bin"

    # ── Upload to MinIO ───────────────────────────────────────────────────────
    storage.upload(
        bucket=settings.MINIO_EVIDENCE_BUCKET,
        key=storage_key,
        data=io.BytesIO(file_bytes),
        size=file_size,
        content_type=detected_mime,
    )

    # ── Persist evidence record ───────────────────────────────────────────────
    evidence = Evidence(
        uploaded_by=current_user.id,
        filename=file.filename or "unknown",
        storage_key=storage_key,
        file_size=file_size,
        mime_type=detected_mime,
        sha256_hash=sha256,
        media_type=media_type,
        status=EvidenceStatus.pending,
        ip_address=request.client.host,
    )
    db.add(evidence)
    await db.flush()

    # ── Audit log ─────────────────────────────────────────────────────────────
    db.add(AuditLog(
        user_id=current_user.id,
        event_type=AuditEventType.upload,
        resource_id=evidence.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        details={"filename": file.filename, "sha256": sha256, "size": file_size},
    ))
    return evidence


@router.get("", response_model=list[EvidenceResponse])
async def list_evidence(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
    skip: int = 0,
    limit: int = 20,
):
    result = await db.execute(
        select(Evidence)
        .where(Evidence.uploaded_by == current_user.id, Evidence.is_deleted == False)
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    result = await db.execute(
        select(Evidence).where(Evidence.id == evidence_id, Evidence.is_deleted == False)
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    if evidence.uploaded_by != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return evidence


@router.delete("/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_evidence(
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    evidence.is_deleted = True  # Soft-delete only
