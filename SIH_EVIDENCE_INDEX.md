# SIH Final Deliverable Evidence Index & Traceability Matrix

**Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System**  
**SIH Final Submission Document — Traceability Matrix**

---

## 1. Requirements Traceability Matrix

| Requirement | Implemented Component | Location in Code / UI | Verification Test | Evidence & Verification Result |
|---|---|---|---|---|
| **Applicant Registration & Auth** | JWT Authentication & Argon2 Hash | `apps/api/routers/auth.py`<br>`apps/api/security/jwt.py`<br>`apps/web/app/login/page.tsx` | `test_unauthenticated_request_returns_401`<br>`test_expired_token_returns_401` | **PASS**: Passwords hashed, tokens expire in 15m, 401 on expired tokens. |
| **Scheme Catalogue & Versioning** | Versioned Scheme Engine | `apps/api/models/scheme.py`<br>`apps/api/routers/schemes.py`<br>`apps/web/app/schemes/page.tsx` | `test_published_version_immutability`<br>`test_version_evaluation` | **PASS**: Published scheme versions are immutable; rule changes generate new versions. |
| **Official Source Attribution** | Mandatory Rule Citation | `apps/api/models/scheme.py`<br>`infra/scripts/seed_schemes.py` | `test_official_source_required` | **PASS**: Every seeded rule cites official MoTA guideline doc, section, and page. |
| **Deterministic Eligibility Engine** | Explainable Rule Evaluator | `apps/api/services/rule_engine.py`<br>`apps/api/routers/applications.py` | `test_rule_engine.py` (6 tests) | **PASS**: Evaluates applicant attributes against scheme rules; returns explainable breakdown. |
| **Application Version Locking** | Locked `scheme_version_id` | `apps/api/models/application.py`<br>`apps/api/routers/applications.py` | `test_applications.py` | **PASS**: Applications lock to `scheme_version_id` at submission; immune to future rule changes. |
| **Dynamic Form Generator** | Schema-Driven Form Renderer | `apps/api/routers/schemes.py`<br>`apps/web/app/applications/[id]/page.tsx` | `test_form_validation.py` | **PASS**: Form fields rendered dynamically based on scheme configuration. |
| **Secure Document Upload** | MIME & Magic Byte Validator | `apps/api/routers/documents.py`<br>`apps/api/storage/local.py` | `test_spoofed_pdf_rejected_by_magic_bytes`<br>`test_path_traversal_filename_rejected` | **PASS**: Spoofed files, traversal filenames, and files >10MB strictly rejected. |
| **Malware Pipeline** | ClamAV Integration Adapter | `apps/api/services/malware_scanner.py` | `test_document_pipeline.py` | **PASS**: Files transition `UPLOADED -> SCANNING -> CLEAN/INFECTED`; infected files quarantined. |
| **AI Document Intelligence** | Multi-Modal Gemini / Vision | `apps/api/ai/gemini.py`<br>`apps/api/routers/processing.py` | `test_document_pipeline.py` | **PASS**: Assists with OCR, quality check, extraction; explicitly non-authoritative. |
| **Human Officer Review** | Officer Work Queue & Scrutiny | `apps/api/routers/cases.py`<br>`apps/web/app/admin/work-queue/page.tsx` | `test_officer_permitted_on_work_queue`<br>`test_officer_assigns_case_with_audit` | **PASS**: Officers claim cases, record notes, review extracted data; applicants blocked (403). |
| **Deficiency Handling** | Deficiency Lifecycle | `apps/api/models/workflow.py`<br>`apps/api/routers/cases.py` | `test_raise_deficiency_creates_all_records`<br>`test_resolve_deficiency_by_officer` | **PASS**: Officers raise deficiency, applicant notified, resubmission updates timeline to closed. |
| **Case Timeline & Notes** | Unified Case Timeline Service | `apps/api/services/timeline_service.py`<br>`apps/api/routers/cases.py` | `test_timeline_hides_internal_events_from_applicants`<br>`test_timeline_idor_protection` | **PASS**: Internal notes hidden from applicants (`is_internal=True`); full audit trail for officers. |
| **In-App Notifications** | Notification Service & Router | `apps/api/services/notification_service.py`<br>`apps/api/routers/notifications.py` | `test_inapp_provider_creates_notification_record`<br>`test_notification_service_suppresses_duplicate` | **PASS**: In-app notices delivered; deduplication window prevents spam; unread counter verified. |
| **Database-Derived Analytics** | SQL Operational Aggregator | `apps/api/routers/analytics.py`<br>`apps/web/app/admin/applications/page.tsx` | `test_analytics.py` (7 tests) | **PASS**: All metrics computed directly from PostgreSQL; zero fabricated government statistics. |
| **Government Integration Adapters** | 5 Truthful External Adapters | `apps/api/integrations/*.py`<br>`apps/web/app/admin/integrations/page.tsx` | `test_gov_integrations.py` (25 tests) | **PASS**: UIDAI, DigiLocker, NSP, DBT, MoTA adapters all report stub/disabled. No fake data. |
| **IDOR & Authorization** | Resource Ownership Checks | `apps/api/security/rbac.py`<br>`apps/api/routers/applications.py` | `test_applicant_cannot_access_other_applicant_application` | **PASS**: Applicants cannot view or edit cross-user records. |
| **Privacy: Aadhaar & Bank** | SHA-256 Hash & AES-256-GCM | `apps/api/models/user.py`<br>`apps/api/services/auth_service.py` | `test_audit_and_security.py` | **PASS**: Aadhaar stored as one-way SHA-256 hash; bank accounts encrypted at rest; masked logs. |
| **Reproducible Local Deployment** | Docker Compose Architecture | `docker-compose.yml`<br>`apps/*/Dockerfile.dev` | YAML parser & Next.js production build | **PASS**: 6 core services defined with internal networking; zero cloud vendor lock-in. |

---

## 2. Master Verification Status Summary
All 18 core functional and security areas have been thoroughly tested, code-verified, and documented with zero regressions.
