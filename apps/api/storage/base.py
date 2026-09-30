"""
StorageService abstract interface.

Business logic MUST only import and use StorageService (the abstract class).
Never import LocalStorageService or S3StorageService directly in routers/services.

Provider selection is handled by get_storage_service() factory.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageService(ABC):

    @abstractmethod
    async def upload(
        self,
        file: BinaryIO,
        key: str,
        content_type: str,
        metadata: dict | None = None,
    ) -> str:
        """Upload a file. Returns the storage key."""
        ...

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download file content by storage key."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a file by storage key."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a file exists at this key."""
        ...

    @abstractmethod
    async def generate_access_url(self, key: str, expires_in_seconds: int = 900) -> str:
        """
        Generate a temporary access URL for the file.

        Local: returns a signed API endpoint URL
        S3: returns a pre-signed URL
        """
        ...

    @abstractmethod
    async def get_file_size(self, key: str) -> int:
        """Return file size in bytes."""
        ...
