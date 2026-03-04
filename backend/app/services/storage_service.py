import io
from datetime import timedelta
from minio import Minio
from app.core.config import settings


class StorageService:
    """Wrapper around MinIO SDK for forensic evidence storage."""

    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self._ensure_buckets()

    def _ensure_buckets(self):
        for bucket in [
            settings.MINIO_EVIDENCE_BUCKET,
            settings.MINIO_RESULTS_BUCKET,
            settings.MINIO_MODELS_BUCKET,
        ]:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    def upload(
        self,
        bucket: str,
        key: str,
        data: io.BytesIO,
        size: int,
        content_type: str,
    ) -> None:
        """Synchronous upload — MinIO SDK is not async."""
        self.client.put_object(
            bucket_name=bucket,
            object_name=key,
            data=data,
            length=size,
            content_type=content_type,
            metadata={"x-forensic-system": "cs-forensics-v1"},
        )

    def download_bytes(self, bucket: str, key: str) -> bytes:
        response = self.client.get_object(bucket, key)
        data: bytes = b""
        try:
            data = bytes(response.read())
        finally:
            response.close()
            response.release_conn()
        return data

    def upload_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(
            bucket_name=bucket,
            object_name=key,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        return self.client.presigned_get_object(
            bucket, key, expires=timedelta(seconds=expires)
        )
