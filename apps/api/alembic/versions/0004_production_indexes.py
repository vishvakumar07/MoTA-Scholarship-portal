"""
Alembic Migration: 0004 - Production Database Indexes
Phase 13: Performance hardening

Adds indexes identified as necessary for production query patterns:
  - applications: (applicant_id, status) composite - officer/admin filtering
  - applications: submitted_at - date-range reporting
  - documents: (application_id, document_status) - scrutiny workflow
  - audit_log: (user_id, created_at) - security investigation
  - audit_log: (entity_type, entity_id) - per-record audit trail
  - notifications: (recipient_id, is_read) - unread notification count
  - scheme_versions: (scheme_id, version_status) - active version lookup
  - gov_verification: (application_id, verification_type) - verification status

All indexes are non-destructive (IF NOT EXISTS).
Safe to apply to production without downtime (CREATE INDEX CONCURRENTLY
is used where applicable — note: requires autocommit mode per Alembic docs).

Rollback: drops the added indexes.
"""

from alembic import op


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Applications: composite index for status-filtered applicant queries
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_applications_applicant_status
        ON applications (applicant_id, status)
    """)

    # Applications: submitted_at for date-range reporting
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_applications_submitted_at
        ON applications (submitted_at)
        WHERE submitted_at IS NOT NULL
    """)

    # Applications: assigned_officer_id for officer workload queries
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_applications_assigned_officer
        ON applications (assigned_officer_id)
        WHERE assigned_officer_id IS NOT NULL
    """)

    # Documents: composite for document workflow per application
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_application_status
        ON documents (application_id, document_status)
    """)

    # Documents: malware scan status for security monitoring
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_documents_scan_status
        ON documents (malware_scan_status)
        WHERE malware_scan_status != 'clean'
    """)

    # Scheme versions: active version lookup per scheme
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_scheme_versions_scheme_status
        ON scheme_versions (scheme_id, version_status)
    """)

    # Notifications: unread count per recipient
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_notifications_recipient_unread
        ON notifications (recipient_id, is_read)
        WHERE is_read = false
    """)

    # Audit log: per-user timeline for security investigation
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_audit_log_user_created
        ON audit_log (user_id, created_at DESC)
        WHERE user_id IS NOT NULL
    """)

    # Audit log: per-entity audit trail
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_audit_log_entity
        ON audit_log (entity_type, entity_id)
        WHERE entity_id IS NOT NULL
    """)

    # Gov verification: per-application verification status
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_gov_verification_app_type
        ON gov_verification_records (application_id, verification_type)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_applications_applicant_status")
    op.execute("DROP INDEX IF EXISTS ix_applications_submitted_at")
    op.execute("DROP INDEX IF EXISTS ix_applications_assigned_officer")
    op.execute("DROP INDEX IF EXISTS ix_documents_application_status")
    op.execute("DROP INDEX IF EXISTS ix_documents_scan_status")
    op.execute("DROP INDEX IF EXISTS ix_scheme_versions_scheme_status")
    op.execute("DROP INDEX IF EXISTS ix_notifications_recipient_unread")
    op.execute("DROP INDEX IF EXISTS ix_audit_log_user_created")
    op.execute("DROP INDEX IF EXISTS ix_audit_log_entity")
    op.execute("DROP INDEX IF EXISTS ix_gov_verification_app_type")
