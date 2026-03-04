import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_private_key: Optional[str] = None
_public_key: Optional[str] = None


def _load_keys() -> tuple[str, str]:
    global _private_key, _public_key
    if not _private_key:
        _private_key = Path(settings.JWT_PRIVATE_KEY_PATH).read_text()
        _public_key  = Path(settings.JWT_PUBLIC_KEY_PATH).read_text()
    return _private_key, _public_key


# ── Password Hashing ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── File Hashing ──────────────────────────────────────────────────────────────

def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hex digest of file bytes for forensic integrity."""
    return hashlib.sha256(data).hexdigest()


# ── JWT Tokens ────────────────────────────────────────────────────────────────

def create_access_token(user_id: str, role: str) -> str:
    private_key, _ = _load_keys()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub":  str(user_id),
        "role": role,
        "type": "access",
        "exp":  expire,
        "jti":  str(uuid.uuid4()),
    }
    return jwt.encode(payload, private_key, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Returns (token_string, jti) — jti is stored in Redis for revocation."""
    private_key, _ = _load_keys()
    jti    = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub":  str(user_id),
        "type": "refresh",
        "exp":  expire,
        "jti":  jti,
    }
    token = jwt.encode(payload, private_key, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    _, public_key = _load_keys()
    return jwt.decode(token, public_key, algorithms=[settings.JWT_ALGORITHM])
