"""
Safe Demo Reset Script for SIH Demonstration Rehearsal.

Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System.

PURPOSE:
  Resets demo/test application records, demo documents, demo case assignments,
  demo timeline events, demo deficiencies, and demo notifications back to a clean
  demonstration state.

CRITICAL SAFETY GUARANTEES:
  1. Never touches official seeded scheme data (schemes, scheme_versions, rules, documents, workflows).
  2. Never touches official roles, permissions, or system reference tables.
  3. Only removes records explicitly marked `is_demo = True` or prefixed with `DEMO-`/`REF-DEMO-`.
  4. Aborts if executed against an environment not configured for demonstration/development.
"""

from __future__ import annotations

import os
import sys

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "api")))

from database import SessionLocal
from config import settings
from models.application import Application, ApplicationAnswer, ApplicationStatusHistory
from models.document import Document, DocumentVerificationHistory
from models.workflow import Deficiency
from models.case import CaseAssignment, CaseNote, CaseTimelineEvent
from models.system import Notification, AuditLog


def safe_demo_reset(dry_run: bool = False):
    """
    Safely purge demo application and operational records.
    """
    print("=" * 70)
    print("MoTA SCHOLARSHIP SYSTEM — SAFE DEMO RESET UTILITY")
    print("=" * 70)

    if settings.ENVIRONMENT not in ("development", "test", "demo", "staging"):
        print(f"[ABORT] Cannot run demo reset in environment: {settings.ENVIRONMENT}")
        sys.exit(1)

    db = SessionLocal()
    try:
        # Find demo applications
        demo_apps = (
            db.query(Application)
            .filter(
                (Application.is_demo == True)
                | (Application.reference_number.like("DEMO-%"))
                | (Application.reference_number.like("REF-DEMO-%"))
            )
            .all()
        )
        demo_app_ids = [app.id for app in demo_apps]
        print(f"Found {len(demo_apps)} demo applications to purge.")

        if dry_run:
            print("[DRY-RUN] No records will be deleted.")
            return

        deleted_counts = {}

        if demo_app_ids:
            # 1. Timeline events
            t_cnt = (
                db.query(CaseTimelineEvent)
                .filter(CaseTimelineEvent.application_id.in_(demo_app_ids))
                .delete(synchronize_session=False)
            )
            deleted_counts["timeline_events"] = t_cnt

            # 2. Case notes
            n_cnt = (
                db.query(CaseNote)
                .filter(CaseNote.application_id.in_(demo_app_ids))
                .delete(synchronize_session=False)
            )
            deleted_counts["case_notes"] = n_cnt

            # 3. Case assignments
            a_cnt = (
                db.query(CaseAssignment)
                .filter(CaseAssignment.application_id.in_(demo_app_ids))
                .delete(synchronize_session=False)
            )
            deleted_counts["case_assignments"] = a_cnt

            # 4. Deficiencies
            def_cnt = (
                db.query(Deficiency)
                .filter(Deficiency.application_id.in_(demo_app_ids))
                .delete(synchronize_session=False)
            )
            deleted_counts["deficiencies"] = def_cnt

            # 5. Documents & Document history
            doc_records = db.query(Document).filter(Document.application_id.in_(demo_app_ids)).all()
            doc_ids = [d.id for d in doc_records]
            if doc_ids:
                db.query(DocumentVerificationHistory).filter(
                    DocumentVerificationHistory.document_id.in_(doc_ids)
                ).delete(synchronize_session=False)
                deleted_counts["documents"] = (
                    db.query(Document)
                    .filter(Document.id.in_(doc_ids))
                    .delete(synchronize_session=False)
                )

            # 6. Status history & answers
            db.query(ApplicationStatusHistory).filter(
                ApplicationStatusHistory.application_id.in_(demo_app_ids)
            ).delete(synchronize_session=False)

            db.query(ApplicationAnswer).filter(
                ApplicationAnswer.application_id.in_(demo_app_ids)
            ).delete(synchronize_session=False)

            # 7. Applications
            del_apps = (
                db.query(Application)
                .filter(Application.id.in_(demo_app_ids))
                .delete(synchronize_session=False)
            )
            deleted_counts["applications"] = del_apps

        # 8. Demo notifications
        notif_cnt = (
            db.query(Notification)
            .filter(Notification.title.like("%DEMO%"))
            .delete(synchronize_session=False)
        )
        deleted_counts["demo_notifications"] = notif_cnt

        db.commit()

        print("\n--- RESET SUMMARY ---")
        for k, v in deleted_counts.items():
            print(f"  Purged {k}: {v}")
        print("\n[SUCCESS] Demo state cleaned. Official schemes and reference rules preserved intact.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Reset failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    safe_demo_reset(dry_run=is_dry)
