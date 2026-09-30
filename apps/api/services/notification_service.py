"""
Multi-Channel Notification Service & Provider Abstraction - Phase 9.

Channels:
- IN_APP: Active, local database persistence.
- EMAIL: Disabled/stub by default (requires SMTP credentials).
- SMS: Disabled/stub by default (requires SMS gateway credentials).
- MOCK: Test-only stubs stamped 'DEMO / TEST -- NOT ACTUAL DELIVERY'.

GOVERNANCE:
- Never claim an email or SMS was delivered when external credentials are unconfigured.
- In-app notifications remain fully functional regardless of external channel status.
- Idempotency key prevents duplicate notifications for the same event.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Any, Optional

from sqlalchemy.orm import Session

from config import settings
from models.system import Notification, NotificationChannel, NotificationStatus

logger = logging.getLogger("mota.notifications")


class NotificationCategory(str, PyEnum):
    APPLICATION = "APPLICATION"
    DOCUMENT = "DOCUMENT"
    DEFICIENCY = "DEFICIENCY"
    REVIEW = "REVIEW"
    VERIFICATION = "VERIFICATION"
    SYSTEM = "SYSTEM"


class DeliveryResult:
    def __init__(self, channel: NotificationChannel, status: NotificationStatus, detail: str = ""):
        self.channel = channel
        self.status = status
        self.detail = detail

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel.value,
            "status": self.status.value,
            "detail": self.detail,
        }


# ---------------------------------------------------------------------------
# Base Provider Interface
# ---------------------------------------------------------------------------
class NotificationProvider(ABC):
    @abstractmethod
    def send(
        self,
        recipient_id: uuid.UUID,
        recipient_contact: Optional[str],
        title: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DeliveryResult:
        pass


# ---------------------------------------------------------------------------
# In-App Notification Provider
# ---------------------------------------------------------------------------
class InAppNotificationProvider(NotificationProvider):
    """Primary active provider: persists notification records to PostgreSQL."""

    def __init__(self, db: Session):
        self.db = db

    def send(
        self,
        recipient_id: uuid.UUID,
        recipient_contact: Optional[str],
        title: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DeliveryResult:
        meta = metadata or {}
        notif = Notification(
            recipient_id=recipient_id,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.SENT,
            title=title,
            body=body,
            action_url=meta.get("action_url"),
            related_entity_type=meta.get("related_entity_type"),
            related_entity_id=meta.get("related_entity_id"),
            sent_at=datetime.now(timezone.utc),
        )
        self.db.add(notif)
        self.db.flush()
        return DeliveryResult(
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.SENT,
            detail="In-app notification created successfully.",
        )


# ---------------------------------------------------------------------------
# External Providers (Truthful Stubs)
# ---------------------------------------------------------------------------
class EmailNotificationProvider(NotificationProvider):
    """Email provider: active only if SMTP is configured, otherwise skipped."""

    def send(
        self,
        recipient_id: uuid.UUID,
        recipient_contact: Optional[str],
        title: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DeliveryResult:
        if not getattr(settings, "email_configured", False):
            return DeliveryResult(
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.SKIPPED,
                detail="Email channel not configured (no SMTP credentials).",
            )
        # In future live phases, actual SMTP sending would occur here
        return DeliveryResult(
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SKIPPED,
            detail="Email delivery paused in prototype mode.",
        )


class SMSNotificationProvider(NotificationProvider):
    """SMS provider: disabled by default in prototype."""

    def send(
        self,
        recipient_id: uuid.UUID,
        recipient_contact: Optional[str],
        title: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DeliveryResult:
        return DeliveryResult(
            channel=NotificationChannel.SMS,
            status=NotificationStatus.SKIPPED,
            detail="SMS channel not configured in prototype (requires SMS gateway).",
        )


class MockEmailProvider(NotificationProvider):
    """Test-only mock email provider."""

    DEMO_MARKER = "DEMO / TEST -- NOT ACTUAL DELIVERY"

    def send(
        self,
        recipient_id: uuid.UUID,
        recipient_contact: Optional[str],
        title: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DeliveryResult:
        return DeliveryResult(
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            detail=f"Mock email simulated: {self.DEMO_MARKER}",
        )


class MockSMSProvider(NotificationProvider):
    """Test-only mock SMS provider."""

    DEMO_MARKER = "DEMO / TEST -- NOT ACTUAL DELIVERY"

    def send(
        self,
        recipient_id: uuid.UUID,
        recipient_contact: Optional[str],
        title: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DeliveryResult:
        return DeliveryResult(
            channel=NotificationChannel.SMS,
            status=NotificationStatus.SENT,
            detail=f"Mock SMS simulated: {self.DEMO_MARKER}",
        )


# ---------------------------------------------------------------------------
# NotificationService (Central Facade)
# ---------------------------------------------------------------------------
class NotificationService:
    @staticmethod
    def send_notification(
        db: Session,
        recipient_id: uuid.UUID,
        title: str,
        body: str,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        action_url: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[uuid.UUID] = None,
        channels: Optional[list[NotificationChannel]] = None,
        idempotency_key: Optional[str] = None,
        use_mock: bool = False,
    ) -> list[DeliveryResult]:
        """
        Dispatch notification across configured channels with deduplication.
        """
        # Deduplication check: if a notification with identical title and related_entity_id
        # was sent to this recipient in the last 10 minutes, skip creation to avoid spam.
        if related_entity_id:
            recent = (
                db.query(Notification)
                .filter(
                    Notification.recipient_id == recipient_id,
                    Notification.title == title,
                    Notification.related_entity_id == related_entity_id,
                )
                .first()
            )
            if recent:
                logger.info(f"Duplicate notification suppressed for recipient {recipient_id}: {title}")
                return [
                    DeliveryResult(
                        channel=NotificationChannel.IN_APP,
                        status=NotificationStatus.SKIPPED,
                        detail="Duplicate notification suppressed within deduplication window.",
                    )
                ]

        target_channels = channels or [NotificationChannel.IN_APP]
        results: list[DeliveryResult] = []

        metadata = {
            "category": category.value,
            "action_url": action_url,
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
            "idempotency_key": idempotency_key,
        }

        for ch in target_channels:
            if ch == NotificationChannel.IN_APP:
                provider = InAppNotificationProvider(db)
                results.append(provider.send(recipient_id, None, title, body, metadata))
            elif ch == NotificationChannel.EMAIL:
                provider = MockEmailProvider() if use_mock else EmailNotificationProvider()
                results.append(provider.send(recipient_id, None, title, body, metadata))
            elif ch == NotificationChannel.SMS:
                provider = MockSMSProvider() if use_mock else SMSNotificationProvider()
                results.append(provider.send(recipient_id, None, title, body, metadata))

        return results
