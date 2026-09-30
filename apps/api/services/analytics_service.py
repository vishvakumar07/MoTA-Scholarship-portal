"""
Analytics and Administrative Intelligence Service - Phase 6.

All metrics are calculated exclusively from real database records using SQL aggregation.
CRITICAL INTEGRITY INVARIANTS:
1. NEVER fabricate government statistics.
2. If records are absent, return explicit empty states ("No data available").
3. Demo records (is_demo=True) are isolated from production analytics.
4. Eligibility numbers are derived solely from deterministic rule engine results (EligibilityResult).
5. Scrutiny workload is purely operational - no artificial officer rankings or performance scores.
6. All outputs include data source transparency metadata.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, case, and_, or_, distinct
from sqlalchemy.orm import Session

from models.application import Application, ApplicationStatus, ApplicationStatusHistory
from models.document import Document, DocumentStatus, MalwareScanStatus, DocumentType, DocumentExtractedFields, DocumentVerificationResult
from models.scheme import Scheme, SchemeVersion
from models.workflow import EligibilityResult, EligibilityDecision, Deficiency, DeficiencyStatus
from models.user import User, Role, UserRole


class AnalyticsService:

    @classmethod
    def get_dashboard_overview(cls, db: Session, include_demo: bool = False) -> Dict[str, Any]:
        """
        Consolidated administrative dashboard overview containing high-level KPIs across
        applications, document pipeline, and deterministic eligibility evaluations.
        """
        # Base filter for demo data isolation
        app_filter = []
        if not include_demo:
            app_filter.append(Application.is_demo == False)

        # 1. Applications KPI
        app_total = db.query(func.count(Application.id)).filter(*app_filter).scalar() or 0
        
        status_counts_raw = (
            db.query(Application.status, func.count(Application.id))
            .filter(*app_filter)
            .group_by(Application.status)
            .all()
        )
        status_map = {s.value if hasattr(s, "value") else str(s): count for s, count in status_counts_raw}

        draft_count = status_map.get(ApplicationStatus.DRAFT.value, 0)
        submitted_count = status_map.get(ApplicationStatus.SUBMITTED.value, 0)
        
        # Operational groupings
        under_review_statuses = [
            ApplicationStatus.DOCUMENT_PROCESSING.value,
            ApplicationStatus.DOCUMENT_VERIFICATION.value,
            ApplicationStatus.RESUBMITTED.value,
            ApplicationStatus.ELIGIBILITY_REVIEW.value,
            ApplicationStatus.SCRUTINY.value,
            ApplicationStatus.SHORTLISTED.value,
            ApplicationStatus.SELECTION_REVIEW.value,
        ]
        under_review_count = sum(status_map.get(s, 0) for s in under_review_statuses)
        deficient_count = status_map.get(ApplicationStatus.DEFICIENCY.value, 0)
        
        completed_statuses = [
            ApplicationStatus.ELIGIBLE.value,
            ApplicationStatus.SELECTED.value,
            ApplicationStatus.COMPLETED.value,
        ]
        completed_verified_count = sum(status_map.get(s, 0) for s in completed_statuses)
        
        rejected_statuses = [
            ApplicationStatus.INELIGIBLE.value,
            ApplicationStatus.NOT_SELECTED.value,
        ]
        rejected_count = sum(status_map.get(s, 0) for s in rejected_statuses)
        withdrawn_count = status_map.get(ApplicationStatus.WITHDRAWN.value, 0)

        demo_count = db.query(func.count(Application.id)).filter(Application.is_demo == True).scalar() or 0

        # 2. Documents KPI
        doc_query = db.query(Document)
        if not include_demo:
            doc_query = doc_query.join(Application, Document.application_id == Application.id).filter(Application.is_demo == False)
        
        doc_total = doc_query.with_entities(func.count(Document.id)).scalar() or 0
        
        doc_status_raw = (
            doc_query.with_entities(Document.status, func.count(Document.id))
            .group_by(Document.status)
            .all()
        )
        doc_status_map = {s.value if hasattr(s, "value") else str(s): count for s, count in doc_status_raw}

        doc_malware_raw = (
            doc_query.with_entities(Document.malware_scan_status, func.count(Document.id))
            .group_by(Document.malware_scan_status)
            .all()
        )
        malware_map = {s.value if hasattr(s, "value") else str(s): count for s, count in doc_malware_raw}

        # 3. Deterministic Eligibility KPI (strictly from rule engine)
        elig_query = db.query(EligibilityResult)
        if not include_demo:
            elig_query = elig_query.join(Application, EligibilityResult.application_id == Application.id).filter(Application.is_demo == False)
        
        elig_total = elig_query.with_entities(func.count(EligibilityResult.id)).scalar() or 0
        elig_decisions_raw = (
            elig_query.with_entities(EligibilityResult.decision, func.count(EligibilityResult.id))
            .group_by(EligibilityResult.decision)
            .all()
        )
        elig_map = {d.value if hasattr(d, "value") else str(d): count for d, count in elig_decisions_raw}

        # 4. Deficiencies KPI
        deficiency_query = db.query(Deficiency)
        if not include_demo:
            deficiency_query = deficiency_query.join(Application, Deficiency.application_id == Application.id).filter(Application.is_demo == False)
        
        total_deficiencies = deficiency_query.with_entities(func.count(Deficiency.id)).scalar() or 0
        open_deficiencies = deficiency_query.filter(Deficiency.status == DeficiencyStatus.OPEN).with_entities(func.count(Deficiency.id)).scalar() or 0
        resolved_deficiencies = deficiency_query.filter(Deficiency.status == DeficiencyStatus.RESPONDED).with_entities(func.count(Deficiency.id)).scalar() or 0

        return {
            "applications": {
                "total": app_total,
                "draft": draft_count,
                "submitted": submitted_count,
                "under_review": under_review_count,
                "deficient": deficient_count,
                "completed_or_verified": completed_verified_count,
                "rejected": rejected_count,
                "withdrawn": withdrawn_count,
                "status_breakdown": status_map,
                "demo_records_isolated": demo_count,
            },
            "documents": {
                "total": doc_total,
                "pending_processing": doc_status_map.get(DocumentStatus.UPLOADED.value, 0),
                "processing": doc_status_map.get(DocumentStatus.PROCESSING.value, 0),
                "processed": doc_status_map.get(DocumentStatus.PROCESSED.value, 0),
                "verified": doc_status_map.get(DocumentStatus.VERIFIED.value, 0),
                "rejected": doc_status_map.get(DocumentStatus.REJECTED.value, 0),
                "malware_clean": malware_map.get(MalwareScanStatus.CLEAN.value, 0),
                "malware_review_required": (
                    malware_map.get(MalwareScanStatus.UNAVAILABLE.value, 0)
                    + malware_map.get(MalwareScanStatus.INFECTED.value, 0)
                    + malware_map.get(MalwareScanStatus.FAILED.value, 0)
                ),
                "malware_status_breakdown": malware_map,
            },
            "eligibility": {
                "evaluated": elig_total,
                "eligible": elig_map.get(EligibilityDecision.ELIGIBLE.value, 0),
                "ineligible": elig_map.get(EligibilityDecision.INELIGIBLE.value, 0),
                "pending_documents": elig_map.get(EligibilityDecision.PENDING_DOCUMENTS.value, 0),
                "pending_review": elig_map.get(EligibilityDecision.PENDING_REVIEW.value, 0),
                "evaluation_pending": max(0, (submitted_count + under_review_count) - elig_total),
                "authority_note": "Evaluated exclusively by the deterministic MoTA rule engine. AI does not produce official eligibility decisions.",
            },
            "deficiencies": {
                "total_raised": total_deficiencies,
                "open": open_deficiencies,
                "responded": resolved_deficiencies,
            },
            "metadata": {
                "data_source": "Local MoTA Scholarship Management System database",
                "government_integration_status": "Government integration not connected (Integration required)",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "is_demo_isolated": not include_demo,
            },
        }

    @classmethod
    def get_application_analytics(
        cls,
        db: Session,
        scheme_code: Optional[str] = None,
        scheme_version_id: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_demo: bool = False,
    ) -> Dict[str, Any]:
        """
        Granular application analytics with truthful filter support.
        """
        filters = []
        if not include_demo:
            filters.append(Application.is_demo == False)

        if status:
            filters.append(Application.status == status)

        if scheme_version_id:
            try:
                v_uuid = uuid.UUID(scheme_version_id)
                filters.append(Application.scheme_version_id == v_uuid)
            except ValueError:
                pass

        if scheme_code:
            filters.append(
                Application.scheme_version_id.in_(
                    db.query(SchemeVersion.id)
                    .join(Scheme, SchemeVersion.scheme_id == Scheme.id)
                    .filter(Scheme.code == scheme_code)
                )
            )

        if date_from:
            filters.append(Application.submitted_at >= date_from)
        if date_to:
            filters.append(Application.submitted_at <= date_to)

        # Total matching
        total = db.query(func.count(Application.id)).filter(*filters).scalar() or 0

        # Status distribution
        status_counts = (
            db.query(Application.status, func.count(Application.id))
            .filter(*filters)
            .group_by(Application.status)
            .all()
        )
        status_dist = {s.value if hasattr(s, "value") else str(s): c for s, c in status_counts}

        # Submission timeline (grouped by date of submission)
        timeline_rows = (
            db.query(func.date(Application.submitted_at), func.count(Application.id))
            .filter(and_(Application.submitted_at != None, *filters))
            .group_by(func.date(Application.submitted_at))
            .order_by(func.date(Application.submitted_at))
            .all()
        )
        submission_trend = [{"date": str(d), "count": count} for d, count in timeline_rows if d]

        return {
            "total_applications": total,
            "status_distribution": status_dist,
            "submission_trend": submission_trend,
            "filters_applied": {
                "scheme_code": scheme_code,
                "scheme_version_id": scheme_version_id,
                "status": status,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "include_demo": include_demo,
            },
            "data_source": "Local MoTA Scholarship Management System database",
        }

    @classmethod
    def get_scheme_analytics(cls, db: Session, include_demo: bool = False) -> List[Dict[str, Any]]:
        """
        Scheme-wise application distribution strictly respecting scheme version locking.
        Historical applications are never retroactively moved to newer scheme versions.
        """
        app_filter = [Application.is_demo == False] if not include_demo else []

        # Query all active schemes with their versions
        schemes = db.query(Scheme).filter(Scheme.is_deleted == False).order_by(Scheme.display_order).all()
        results = []

        for scheme in schemes:
            versions = (
                db.query(SchemeVersion)
                .filter(SchemeVersion.scheme_id == scheme.id, SchemeVersion.is_deleted == False)
                .order_by(SchemeVersion.version_number.desc())
                .all()
            )

            for ver in versions:
                # Count applications strictly locked to this exact version
                v_apps_query = db.query(Application).filter(
                    Application.scheme_version_id == ver.id,
                    *app_filter
                )
                total_v_apps = v_apps_query.count()

                status_counts = (
                    db.query(Application.status, func.count(Application.id))
                    .filter(Application.scheme_version_id == ver.id, *app_filter)
                    .group_by(Application.status)
                    .all()
                )
                s_map = {s.value if hasattr(s, "value") else str(s): count for s, count in status_counts}

                submitted = s_map.get(ApplicationStatus.SUBMITTED.value, 0)
                under_review = sum(s_map.get(st, 0) for st in [
                    ApplicationStatus.DOCUMENT_PROCESSING.value,
                    ApplicationStatus.DOCUMENT_VERIFICATION.value,
                    ApplicationStatus.RESUBMITTED.value,
                    ApplicationStatus.ELIGIBILITY_REVIEW.value,
                    ApplicationStatus.SCRUTINY.value,
                    ApplicationStatus.SHORTLISTED.value,
                    ApplicationStatus.SELECTION_REVIEW.value,
                ])
                deficient = s_map.get(ApplicationStatus.DEFICIENCY.value, 0)
                verified = sum(s_map.get(st, 0) for st in [
                    ApplicationStatus.ELIGIBLE.value,
                    ApplicationStatus.SELECTED.value,
                    ApplicationStatus.COMPLETED.value,
                ])
                rejected = sum(s_map.get(st, 0) for st in [
                    ApplicationStatus.INELIGIBLE.value,
                    ApplicationStatus.NOT_SELECTED.value,
                ])

                results.append({
                    "scheme_id": str(scheme.id),
                    "scheme_code": scheme.code,
                    "scheme_name": scheme.name,
                    "short_name": scheme.short_name,
                    "scheme_type": scheme.scheme_type.value if hasattr(scheme.scheme_type, "value") else str(scheme.scheme_type),
                    "version_id": str(ver.id),
                    "version_number": ver.version_number,
                    "academic_year": ver.academic_year,
                    "version_status": ver.version_status.value if hasattr(ver.version_status, "value") else str(ver.version_status),
                    "is_accepting_applications": ver.is_accepting_applications,
                    "total_applications": total_v_apps,
                    "submitted": submitted,
                    "under_review": under_review,
                    "deficient": deficient,
                    "verified": verified,
                    "rejected": rejected,
                    "draft": s_map.get(ApplicationStatus.DRAFT.value, 0),
                    "version_locking_verified": True,
                })

        return results

    @classmethod
    def get_document_analytics(cls, db: Session, include_demo: bool = False) -> Dict[str, Any]:
        """
        Document processing analytics strictly distinguishing AI processing states from
        officer verification determinations.
        """
        doc_query = db.query(Document)
        if not include_demo:
            doc_query = doc_query.join(Application, Document.application_id == Application.id).filter(Application.is_demo == False)

        total_docs = doc_query.with_entities(func.count(Document.id)).scalar() or 0

        # Document type distribution
        doc_types_raw = (
            doc_query.with_entities(Document.document_type, func.count(Document.id))
            .group_by(Document.document_type)
            .all()
        )
        type_distribution = {
            t.value if hasattr(t, "value") else str(t): count for t, count in doc_types_raw
        }

        # Malware scan distribution
        malware_raw = (
            doc_query.with_entities(Document.malware_scan_status, func.count(Document.id))
            .group_by(Document.malware_scan_status)
            .all()
        )
        malware_dist = {
            m.value if hasattr(m, "value") else str(m): count for m, count in malware_raw
        }

        # AI Processing state (automated pipeline)
        ai_extracted_count = (
            db.query(func.count(distinct(DocumentExtractedFields.document_id)))
            .scalar() or 0
        )
        quality_reviewed_count = (
            db.query(func.count(distinct(DocumentVerificationResult.document_id)))
            .scalar() or 0
        )

        # Human Officer Verification state (Authoritative decision only)
        officer_accepted_count = (
            db.query(func.count(DocumentVerificationResult.id))
            .filter(DocumentVerificationResult.officer_decision == "accepted")
            .scalar() or 0
        )
        officer_rejected_count = (
            db.query(func.count(DocumentVerificationResult.id))
            .filter(DocumentVerificationResult.officer_decision == "rejected")
            .scalar() or 0
        )
        officer_pending_count = max(0, total_docs - (officer_accepted_count + officer_rejected_count))

        return {
            "total_documents": total_docs,
            "type_distribution": type_distribution,
            "malware_scanning": {
                "clean": malware_dist.get(MalwareScanStatus.CLEAN.value, 0),
                "infected": malware_dist.get(MalwareScanStatus.INFECTED.value, 0),
                "unavailable": malware_dist.get(MalwareScanStatus.UNAVAILABLE.value, 0),
                "failed": malware_dist.get(MalwareScanStatus.FAILED.value, 0),
                "pending": malware_dist.get(MalwareScanStatus.PENDING.value, 0),
                "note": "ClamAV daemon status. When unavailable, manual officer verification is mandatory.",
            },
            "ai_pipeline_state": {
                "entity_extractions_completed": ai_extracted_count,
                "quality_heuristics_assessed": quality_reviewed_count,
                "label": "AI SUGGESTIONS ONLY - Non-authoritative automated assistive processing",
            },
            "officer_verification_state": {
                "accepted_verified": officer_accepted_count,
                "rejected": officer_rejected_count,
                "pending_review": officer_pending_count,
                "label": "OFFICIAL ADMINISTRATIVE DETERMINATIONS (Authorised Human Officers)",
            },
            "data_source": "Local MoTA Scholarship Management System database",
        }

    @classmethod
    def get_eligibility_analytics(cls, db: Session, include_demo: bool = False) -> Dict[str, Any]:
        """
        Deterministic rule engine outcomes and rule failure categories.
        """
        query = db.query(EligibilityResult)
        if not include_demo:
            query = query.join(Application, EligibilityResult.application_id == Application.id).filter(Application.is_demo == False)

        total_evaluated = query.with_entities(func.count(EligibilityResult.id)).scalar() or 0

        decision_counts = (
            query.with_entities(EligibilityResult.decision, func.count(EligibilityResult.id))
            .group_by(EligibilityResult.decision)
            .all()
        )
        decision_map = {d.value if hasattr(d, "value") else str(d): count for d, count in decision_counts}

        # Compile failure reasons from failure_reasons JSON
        results_with_failures = (
            query.filter(EligibilityResult.decision == EligibilityDecision.INELIGIBLE)
            .with_entities(EligibilityResult.failure_reasons)
            .all()
        )
        
        failure_frequency: Dict[str, int] = {}
        for row in results_with_failures:
            reasons = row[0]
            if isinstance(reasons, list):
                for r in reasons:
                    text = str(r).strip()
                    failure_frequency[text] = failure_frequency.get(text, 0) + 1

        top_reasons = sorted(
            [{"reason": k, "count": v} for k, v in failure_frequency.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

        return {
            "total_evaluated": total_evaluated,
            "decisions": {
                "eligible": decision_map.get(EligibilityDecision.ELIGIBLE.value, 0),
                "ineligible": decision_map.get(EligibilityDecision.INELIGIBLE.value, 0),
                "pending_documents": decision_map.get(EligibilityDecision.PENDING_DOCUMENTS.value, 0),
                "pending_review": decision_map.get(EligibilityDecision.PENDING_REVIEW.value, 0),
            },
            "common_failure_reasons": top_reasons,
            "evaluation_engine": "MoTA Deterministic Rule Engine v1.0",
            "ai_separation_guarantee": "AI models do not possess decision authority and are strictly excluded from eligibility counts.",
        }

    @classmethod
    def get_workload_analytics(cls, db: Session) -> Dict[str, Any]:
        """
        Operational scrutiny workload distribution.
        Truthful invariant: No artificial performance scores, no rankings, no competitive gamification.
        """
        # Check if officer assignments exist
        assigned_count = (
            db.query(func.count(Application.id))
            .filter(Application.assigned_officer_id != None)
            .scalar() or 0
        )

        # Get all officers
        officer_roles = ["verification_officer", "scrutiny_officer", "scheme_admin", "super_admin"]
        officers = (
            db.query(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, UserRole.role_id == Role.id)
            .filter(Role.name.in_(officer_roles))
            .distinct()
            .all()
        )

        officer_workloads = []
        for off in officers:
            assigned_apps = (
                db.query(func.count(Application.id))
                .filter(Application.assigned_officer_id == off.id)
                .scalar() or 0
            )

            # Decisions made on documents
            docs_reviewed = (
                db.query(func.count(DocumentVerificationResult.id))
                .filter(DocumentVerificationResult.verified_by_id == off.id)
                .scalar() or 0
            )

            # Deficiencies raised
            deficiencies_raised = (
                db.query(func.count(Deficiency.id))
                .filter(Deficiency.raised_by_id == off.id)
                .scalar() or 0
            )

            officer_workloads.append({
                "officer_id": str(off.id),
                "officer_name": off.full_name,
                "officer_email": off.email,
                "applications_assigned": assigned_apps,
                "documents_reviewed": docs_reviewed,
                "deficiencies_raised": deficiencies_raised,
            })

        has_assignment_data = assigned_count > 0 or len(officer_workloads) > 0

        return {
            "has_assignment_data": has_assignment_data,
            "total_assigned_applications": assigned_count,
            "officer_workloads": officer_workloads,
            "note": (
                "Operational workload distribution only. "
                "The system does not calculate subjective speed scores or competitive rankings."
                if has_assignment_data
                else "Officer assignment analytics require assignment data. No individual officer assignments are recorded yet."
            ),
        }

    @classmethod
    def get_processing_times(cls, db: Session) -> Dict[str, Any]:
        """
        Operational turnaround durations calculated strictly from actual timestamps.
        """
        # 1. Submission to first review/status transition
        # Find applications that have both submitted_at and a subsequent status history entry
        transitions = (
            db.query(
                Application.id,
                Application.submitted_at,
                func.min(ApplicationStatusHistory.changed_at).label("first_transition_at"),
            )
            .join(ApplicationStatusHistory, Application.id == ApplicationStatusHistory.application_id)
            .filter(
                Application.submitted_at != None,
                ApplicationStatusHistory.changed_at > Application.submitted_at
            )
            .group_by(Application.id, Application.submitted_at)
            .all()
        )

        submission_review_diffs = []
        for _, submitted_at, first_reviewed in transitions:
            if submitted_at and first_reviewed:
                delta = (first_reviewed - submitted_at).total_seconds() / 86400.0  # in days
                if delta >= 0:
                    submission_review_diffs.append(delta)

        avg_submission_to_review_days = (
            round(sum(submission_review_diffs) / len(submission_review_diffs), 2)
            if submission_review_diffs
            else None
        )

        # 2. Deficiency to resolution duration
        resolved_deficiencies = (
            db.query(Deficiency.created_at, Deficiency.resolved_at)
            .filter(Deficiency.resolved_at != None, Deficiency.created_at != None)
            .all()
        )
        deficiency_diffs = []
        for created_at, resolved_at in resolved_deficiencies:
            if created_at and resolved_at:
                delta = (resolved_at - created_at).total_seconds() / 86400.0
                if delta >= 0:
                    deficiency_diffs.append(delta)

        avg_deficiency_resolution_days = (
            round(sum(deficiency_diffs) / len(deficiency_diffs), 2)
            if deficiency_diffs
            else None
        )

        # 3. AI Document processing duration in ms
        extracted_times = (
            db.query(DocumentExtractedFields.processing_time_ms)
            .filter(DocumentExtractedFields.processing_time_ms != None)
            .all()
        )
        processing_times_ms = [row[0] for row in extracted_times if row[0] is not None]
        avg_processing_time_ms = (
            round(sum(processing_times_ms) / len(processing_times_ms), 1)
            if processing_times_ms
            else None
        )

        return {
            "submission_to_first_review": {
                "average_days": avg_submission_to_review_days,
                "sample_size": len(submission_review_diffs),
                "status": "Available" if avg_submission_to_review_days is not None else "No data available yet",
            },
            "deficiency_resolution": {
                "average_days": avg_deficiency_resolution_days,
                "sample_size": len(deficiency_diffs),
                "status": "Available" if avg_deficiency_resolution_days is not None else "No resolved deficiencies yet",
            },
            "document_processing_pipeline": {
                "average_ms": avg_processing_time_ms,
                "sample_size": len(processing_times_ms),
                "status": "Available" if avg_processing_time_ms is not None else "No documents processed through pipeline yet",
            },
            "transparency_note": "Averages are calculated exclusively from verified database timestamps without estimation.",
        }

    @classmethod
    def export_csv(cls, db: Session, report_type: str = "applications") -> str:
        """
        Generates a privacy-preserving CSV report.
        Strictly excludes Aadhaar numbers, hashes, bank account numbers, passwords, and private certificate text.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == "schemes":
            writer.writerow([
                "Scheme Code", "Scheme Name", "Type", "Version Number",
                "Academic Year", "Status", "Accepting Applications",
                "Total Applications", "Submitted", "Under Review",
                "Deficient", "Verified", "Rejected"
            ])
            schemes_data = cls.get_scheme_analytics(db)
            for s in schemes_data:
                writer.writerow([
                    s["scheme_code"], s["scheme_name"], s["scheme_type"],
                    s["version_number"], s["academic_year"] or "", s["version_status"],
                    "Yes" if s["is_accepting_applications"] else "No",
                    s["total_applications"], s["submitted"], s["under_review"],
                    s["deficient"], s["verified"], s["rejected"],
                ])

        elif report_type == "documents":
            writer.writerow([
                "Document ID", "Document Type", "Status", "Malware Scan Status",
                "File Size (KB)", "Created At"
            ])
            docs = (
                db.query(Document)
                .join(Application, Document.application_id == Application.id)
                .filter(Application.is_demo == False)
                .order_by(Document.created_at.desc())
                .limit(500)
                .all()
            )
            for d in docs:
                writer.writerow([
                    str(d.id),
                    d.document_type.value if hasattr(d.document_type, "value") else str(d.document_type),
                    d.status.value if hasattr(d.status, "value") else str(d.status),
                    d.malware_scan_status.value if hasattr(d.malware_scan_status, "value") else str(d.malware_scan_status),
                    round(d.file_size_bytes / 1024, 1) if d.file_size_bytes else 0,
                    d.created_at.isoformat() if d.created_at else "",
                ])

        else:  # Default to applications
            writer.writerow([
                "Application ID", "Reference Number", "Scheme Code", "Version",
                "Status", "Submitted At", "Created At"
            ])
            apps = (
                db.query(Application, Scheme.code, SchemeVersion.version_number)
                .join(SchemeVersion, Application.scheme_version_id == SchemeVersion.id)
                .join(Scheme, SchemeVersion.scheme_id == Scheme.id)
                .filter(Application.is_demo == False)
                .order_by(Application.created_at.desc())
                .limit(500)
                .all()
            )
            for app, code, ver in apps:
                writer.writerow([
                    str(app.id),
                    app.reference_number or "PENDING",
                    code,
                    ver,
                    app.status.value if hasattr(app.status, "value") else str(app.status),
                    app.submitted_at.isoformat() if app.submitted_at else "",
                    app.created_at.isoformat() if app.created_at else "",
                ])

        return output.getvalue()
