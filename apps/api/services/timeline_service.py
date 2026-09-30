"""
Case Timeline Service - Phase 9.

Aggregates operational lifecycle events for an application.
Enforces privacy boundaries:
- Applicants receive user-facing milestones only (is_internal=False).
- Authorized officers/admins receive the complete audit-grade case timeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from models.application import Application, ApplicationStatusHistory
from models.case import CaseTimelineEvent, TimelineEventType
from models.workflow import Deficiency


class TimelineEventOut:
    def __init__(
        self,
        event_id: str,
        event_type: str,
        title: str,
        description: str,
        timestamp: datetime,
        actor_type: str,
        is_internal: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.event_id = event_id
        self.event_type = event_type
        self.title = title
        self.description = description
        self.timestamp = timestamp
        self.actor_type = actor_type
        self.is_internal = is_internal
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "actor_type": self.actor_type,
            "is_internal": self.is_internal,
            "metadata": self.metadata,
        }


class CaseTimelineService:

    @staticmethod
    def record_event(
        db: Session,
        application_id: uuid.UUID,
        event_type: str,
        title: str,
        description: str,
        actor_type: str = "system",
        actor_id: Optional[uuid.UUID] = None,
        is_internal: bool = False,
        metadata: Optional[dict[str, Any]] = None,
    ) -> CaseTimelineEvent:
        """Record an immutable timeline event."""
        event = CaseTimelineEvent(
            application_id=application_id,
            event_type=event_type,
            title=title,
            description=description,
            actor_type=actor_type,
            actor_id=actor_id,
            is_internal=is_internal,
            event_metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.flush()
        return event

    @staticmethod
    def get_timeline(
        db: Session,
        application_id: uuid.UUID,
        is_staff: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Retrieve unified timeline for an application.
        Combines explicit CaseTimelineEvents, ApplicationStatusHistory, and Deficiencies.
        """
        events: list[TimelineEventOut] = []

        # 1. Query recorded CaseTimelineEvents
        query = db.query(CaseTimelineEvent).filter(CaseTimelineEvent.application_id == application_id)
        if not is_staff:
            query = query.filter(CaseTimelineEvent.is_internal == False)

        recorded = query.all()
        for r in recorded:
            events.append(
                TimelineEventOut(
                    event_id=str(r.id),
                    event_type=r.event_type,
                    title=r.title,
                    description=r.description,
                    timestamp=r.created_at,
                    actor_type=r.actor_type,
                    is_internal=r.is_internal,
                    metadata=r.event_metadata or {},
                )
            )

        # 2. Add events from ApplicationStatusHistory (backward-compatible historical records)
        histories = (
            db.query(ApplicationStatusHistory)
            .filter(ApplicationStatusHistory.application_id == application_id)
            .all()
        )
        for h in histories:
            # Check if already captured in recorded events
            already_captured = any(
                e.event_type == TimelineEventType.APPLICATION_STATUS_CHANGED.value
                and e.timestamp == h.changed_at
                for e in events
            )
            if not already_captured:
                status_label = h.to_status.replace("_", " ").title()
                desc = h.change_reason or f"Application status transitioned to {status_label}."
                if h.system_note and is_staff:
                    desc += f" (Note: {h.system_note})"

                events.append(
                    TimelineEventOut(
                        event_id=str(h.id),
                        event_type=TimelineEventType.APPLICATION_STATUS_CHANGED.value,
                        title=f"Status: {status_label}",
                        description=desc,
                        timestamp=h.changed_at,
                        actor_type="officer" if h.changed_by_id else "system",
                        is_internal=False,
                        metadata={"from_status": h.from_status, "to_status": h.to_status},
                    )
                )

        # 3. Add Deficiencies
        defs = db.query(Deficiency).filter(Deficiency.application_id == application_id).all()
        for d in defs:
            # Deficiency Raised
            if not any(e.event_type == TimelineEventType.DEFICIENCY_RAISED.value and e.metadata.get("deficiency_id") == str(d.id) for e in events):
                events.append(
                    TimelineEventOut(
                        event_id=f"def_raised_{d.id}",
                        event_type=TimelineEventType.DEFICIENCY_RAISED.value,
                        title="Deficiency Notice Issued",
                        description=f"Correction requested: {d.description}",
                        timestamp=d.created_at,
                        actor_type="officer",
                        is_internal=False,
                        metadata={"deficiency_id": str(d.id), "document_type": d.document_type_requested},
                    )
                )

            # Deficiency Responded
            if d.applicant_response and d.resolved_at:
                if not any(e.event_type == TimelineEventType.DEFICIENCY_RESPONDED.value and e.metadata.get("deficiency_id") == str(d.id) for e in events):
                    events.append(
                        TimelineEventOut(
                            event_id=f"def_resp_{d.id}",
                            event_type=TimelineEventType.DEFICIENCY_RESPONDED.value,
                            title="Deficiency Response Submitted",
                            description=f"Applicant submitted response: {d.applicant_response[:120]}...",
                            timestamp=d.resolved_at,
                            actor_type="applicant",
                            is_internal=False,
                            metadata={"deficiency_id": str(d.id)},
                        )
                    )

        # Sort all chronologically ascending (earliest to latest)
        events.sort(key=lambda x: x.timestamp or datetime.min.replace(tzinfo=timezone.utc))

        return [e.to_dict() for e in events]
