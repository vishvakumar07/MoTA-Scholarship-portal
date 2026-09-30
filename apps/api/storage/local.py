"""
Local filesystem StorageService implementation.

Used when STORAGE_PROVIDER=local (default for SIH demo).

Files are stored under: {LOCAL_STORAGE_PATH}/documents/{key}
Access is via signed JWT tokens through /api/v1/files/serve/{token}.
Files are NEVER served as public static assets.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import BinaryIO

from storage.base import StorageService


class LocalStorageService(StorageService):

    def __init__(self, base_path: str):
        self.base = Path(base_path)
        # Ensure all subdirectories exist
        for subdir in ["documents", "processed", "temporary", "exports"]:
            (self.base / subdir).mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """Resolve storage key to absolute path. Prevents path traversal."""
        full = (self.base / "documents" / key).resolve()
        # Security: ensure path stays within base directory
        if not str(full).startswith(str(self.base.resolve())):
            raise ValueError(f"Invalid storage key: {key}")
        return full

    async def upload(
        self,
        file: BinaryIO,
        key: str,
        content_type: str,
        metadata: dict | None = None,
    ) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(file.read())
        return key

    async def download(self, key: str) -> bytes:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> None:
        path = self._resolve(key)
        if path.exists():
            path.unlink()

    async def exists(self, key: str) -> bool:
        return self._resolve(key).exists()

    async def generate_access_url(self, key: str, expires_in_seconds: int = 900) -> str:
        """
        Generate a signed JWT-based access URL.
        The token encodes the storage key and expiry.
        Served via GET /api/v1/files/serve/{token}
        """
        import time
        from jose import jwt as jose_jwt
        from config import settings

        payload = {
            "key": key,
            "exp": int(time.time()) + expires_in_seconds,
            "type": "file_access",
        }
        token = jose_jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
        return f"{settings.API_BASE_URL}/api/v1/files/serve/{token}"

    async def get_file_size(self, key: str) -> int:
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return path.stat().st_size


def get_storage_service() -> StorageService:
    """Factory  -  returns the configured storage provider."""
    from config import settings

    if settings.STORAGE_PROVIDER == "s3":
        # S3 implementation  -  to be implemented when cloud deployment is needed
        raise NotImplementedError(
            "S3StorageService not yet implemented. "
            "Set STORAGE_PROVIDER=local for the SIH prototype."
        )

    return LocalStorageService(base_path=settings.LOCAL_STORAGE_PATH)
