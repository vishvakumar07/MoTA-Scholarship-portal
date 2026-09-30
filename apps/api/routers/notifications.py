"""
Notifications router - /api/v1/notifications/*

GET   /api/v1/notifications            - List in-app notifications
POST  /api/v1/notifications/{id}/read  - Mark as read
POST  /api/v1/notifications/read-all   - Mark all as read
GET   /api/v1/notifications/status     - Show notification channel configuration status
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from models.system import Notification, NotificationChannel, NotificationStatus
from schemas.application import NotificationOut, NotificationListResponse
from security.rbac import get_current_user
from models.user import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/status",
    summary="Get notification channel configuration status",
)
def notification_status():
    """
    Returns the configuration status of each notification channel.

    EMAIL and SMS require external credentials.
    If not configured, the channel is clearly marked as NOT_CONFIGURED.
    No fake delivery is performed.
    """
    from config import settings

    return {
        "channels": {
            "in_app": {
                "configured": True,
                "status": "active",
                "note": "In-app notifications are always available.",
            },
            "email": {
                "configured": settings.email_configured,
                "status": "active" if settings.email_configured else "not_configured",
                "note": (
                    "Email notifications require SMTP credentials."
                    if not settings.email_configured
                    else f"Email notifications active via {settings.SMTP_HOST}"
                ),
            },
            "sms": {
                "configured": False,
                "status": "not_configured",
                "note": "SMS notifications require SMS gateway credentials (not configured in this prototype).",
            },
        },
        "disclaimer": (
            "External notification channels (email, SMS) require authorised government "
            "infrastructure credentials. No simulated or fake government communications "
            "are sent by this system."
        ),
    }


@router.get(
    "/unread-count",
    summary="Get unread notification count for the current user",
)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    count = (
        db.query(Notification)
        .filter(
            Notification.recipient_id == current_user.id,
            Notification.channel == NotificationChannel.IN_APP,
            Notification.read_at.is_(None),
        )
        .count()
    )
    return {"unread_count": count}


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List in-app notifications for the current user with pagination and filters",
)
def list_notifications(
    category: Optional[str] = Query(None, description="Optional category filter"),
    unread_only: bool = Query(False, description="Filter to unread notifications only"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.channel == NotificationChannel.IN_APP,
    )

    if unread_only:
        query = query.filter(Notification.read_at.is_(None))

    if category:
        query = query.filter(Notification.title.ilike(f"%{category}%"))

    total = query.count()
    notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

    unread_count = (
        db.query(Notification)
        .filter(
            Notification.recipient_id == current_user.id,
            Notification.channel == NotificationChannel.IN_APP,
            Notification.read_at.is_(None),
        )
        .count()
    )

    return NotificationListResponse(
        notifications=[
            NotificationOut(
                id=str(n.id),
                channel=n.channel.value,
                status=n.status.value,
                title=n.title,
                body=n.body,
                action_url=n.action_url,
                related_entity_type=n.related_entity_type,
                sent_at=n.sent_at,
                read_at=n.read_at,
                created_at=n.created_at,
            )
            for n in notifications
        ],
        total=total,
        unread_count=unread_count,
    )


@router.post(
    "/{notification_id}/read",
    summary="Mark a notification as read",
)
def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")

    if notif.read_at is None:
        notif.read_at = datetime.now(timezone.utc)
        db.commit()

    return {"marked_read": True}


@router.post(
    "/read-all",
    summary="Mark all in-app notifications as read",
)
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.channel == NotificationChannel.IN_APP,
        Notification.read_at.is_(None),
    ).update({"read_at": now}, synchronize_session="fetch")
    db.commit()
    return {"marked_all_read": True}
