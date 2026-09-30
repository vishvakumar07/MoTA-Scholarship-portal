"""
Admin Analytics and Dashboard Router - Phase 6.

Endpoints:
  GET /admin/analytics/dashboard        - Comprehensive high-level KPI cards and overview
  GET /admin/analytics/applications     - Status breakdown, trends, and filterable metrics
  GET /admin/analytics/schemes          - Scheme & version-wise distribution (version locking)
  GET /admin/analytics/documents        - Pipeline processing states & malware scan breakdown
  GET /admin/analytics/eligibility      - Deterministic rule engine evaluation outcomes
  GET /admin/analytics/workload         - Operational officer scrutiny workload
  GET /admin/analytics/processing-times - Empirical turnaround durations
  GET /admin/analytics/export           - Privacy-preserving administrative CSV export
  GET /admin/dashboard                  - Direct dashboard overview alias

MANDATORY INVARIANTS:
  - All metrics are calculated strictly from local database records.
  - Zero fabricated government data or statistics.
  - AI predictions are separated from official eligibility counts.
  - All access is strictly protected by RBAC (officers and admins only).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from security.rbac import get_current_user
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin", tags=["Administrative Analytics & Dashboards (Phase 6)"])


def _require_authorized_staff(user: User) -> None:
    """
    Enforces that the caller has an administrative or scrutiny officer role.
    Applicants are strictly forbidden from viewing administrative analytics.
    """
    roles = [r.name for r in getattr(user, "roles", [])]
    authorized_roles = {
        "super_admin",
        "scheme_admin",
        "scrutiny_officer",
        "verification_officer",
        "selection_committee",
    }
    if not any(r in authorized_roles for r in roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorised administrative and scrutiny officers.",
        )


@router.get(
    "/analytics/dashboard",
    summary="[Admin/Officer] Consolidated administrative dashboard KPIs",
)
@router.get(
    "/dashboard",
    summary="[Admin/Officer] Administrative dashboard overview alias",
)
def get_dashboard_overview(
    include_demo: bool = Query(False, description="Whether to include isolated demo/test applications"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_authorized_staff(current_user)
    return AnalyticsService.get_dashboard_overview(db, include_demo=include_demo)


@router.get(
    "/analytics/applications",
    summary="[Admin/Officer] Application volume and status analytics with filters",
)
def get_application_analytics(
    scheme_code: Optional[str] = Query(None, description="Filter by MoTA scheme code"),
    scheme_version_id: Optional[str] = Query(None, description="Filter by scheme version UUID"),
    status: Optional[str] = Query(None, description="Filter by application status"),
    date_from: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO format)"),
    include_demo: bool = Query(False, description="Include test applications"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_authorized_staff(current_user)
    return AnalyticsService.get_application_analytics(
        db,
        scheme_code=scheme_code,
        scheme_version_id=scheme_version_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        include_demo=include_demo,
    )


@router.get(
    "/analytics/schemes",
    summary="[Admin/Officer] Scheme-wise application breakdown with version locking",
)
def get_scheme_analytics(
    include_demo: bool = Query(False, description="Include test applications"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    _require_authorized_staff(current_user)
    return AnalyticsService.get_scheme_analytics(db, include_demo=include_demo)


@router.get(
    "/analytics/documents",
    summary="[Admin/Officer] Document pipeline and scrutiny breakdown",
)
def get_document_analytics(
    include_demo: bool = Query(False, description="Include test applications"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_authorized_staff(current_user)
    return AnalyticsService.get_document_analytics(db, include_demo=include_demo)


@router.get(
    "/analytics/eligibility",
    summary="[Admin/Officer] Deterministic rule engine evaluation outcomes",
)
def get_eligibility_analytics(
    include_demo: bool = Query(False, description="Include test applications"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_authorized_staff(current_user)
    return AnalyticsService.get_eligibility_analytics(db, include_demo=include_demo)


@router.get(
    "/analytics/workload",
    summary="[Admin/Officer] Operational scrutiny workload distribution",
)
def get_workload_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_authorized_staff(current_user)
    return AnalyticsService.get_workload_analytics(db)


@router.get(
    "/analytics/processing-times",
    summary="[Admin/Officer] Operational turnaround durations from timestamps",
)
def get_processing_times(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_authorized_staff(current_user)
    return AnalyticsService.get_processing_times(db)


@router.get(
    "/analytics/export",
    summary="[Admin/Officer] Export privacy-preserving CSV report",
)
def export_analytics_csv(
    report_type: str = Query("applications", pattern="^(applications|schemes|documents)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    _require_authorized_staff(current_user)
    csv_content = AnalyticsService.export_csv(db, report_type=report_type)
    filename = f"mota_{report_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
