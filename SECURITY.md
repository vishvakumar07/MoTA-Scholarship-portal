# Security Architecture & Evidence Package

**Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System**  
**SIH Final Submission Document — Security & Governance Audit**

---

## 1. Authentication Architecture
- **Password Hashing**: Uses modern cryptographic hashing (Argon2 / bcrypt via PassLib) with unique salts per user.
- **Session & Token Management**:
  - JWT Access Tokens (HS256) with short expiration window (15 minutes).
  - Refresh Tokens stored with rotation and revocable token IDs.
  - Strict Bearer token validation and automatic 401 Unauthorized handling on token tampering or expiry.
- **Health & Info Isolation**: API health checks (`/health`, `/ready`) expose zero credentials, tokens, or sensitive environment details.

## 2. Authorization & Role-Based Access Control (RBAC)
The system enforces strict role-based authorization across 6 designated operational roles:
1. `applicant` — ST student applying for MoTA scholarship/fellowship.
2. `verification_officer` — Institute/District officer verifying documents.
3. `scrutiny_officer` — State/Ministry officer scrutinizing applications.
4. `selection_committee` — Committee member reviewing shortlists and selection.
5. `scheme_admin` — MoTA policy administrator configuring scheme rules and versions.
6. `super_admin` — Technical administrator managing users and platform health.

### RBAC Enforcement Evidence:
- `require_roles(...)` and permission scopes guard all administrative routes.
- Applicants attempting to call `/api/v1/admin/*`, `/api/v1/admin/schemes/*`, or officer work queues receive immediate `403 Forbidden` errors.
- Verified in tests: `test_applicant_blocked_from_admin_scheme_creation`, `test_applicant_blocked_from_work_queue`, `test_applicant_blocked_from_assignment`.

## 3. Insecure Direct Object Reference (IDOR) Protection
- **Application Level**: Applicants can only read and modify their own applications (`application.applicant_id == current_user.id`). Querying another citizen's application returns `403 Forbidden` or `404 Not Found`.
- **Document Level**: Document access requires verified ownership or assigned officer authorization.
- **Notification Level**: Notification retrieval and `/mark-read` verify `notification.recipient_id == current_user.id`. Cross-user tampering is rejected.
- **Timeline Level**: Applicants accessing case timeline only see public lifecycle events. Internal scrutiny notes and officer deliberation events are strictly filtered out (`is_internal == False`).
- Verified in tests: `test_applicant_cannot_access_other_applicant_application`, `test_mark_read_idor_protection`, `test_timeline_idor_protection`.

## 4. File Security & Malware Pipeline
- **Validation**:
  - MIME type checking and file extension whitelist (`.pdf`, `.jpg`, `.jpeg`, `.png`).
  - Magic-byte inspection to prevent spoofed file extensions.
  - Size limitation enforced at 10 MB per file, max 20 documents per application.
  - Path traversal defense: Filenames sanitized using safe basename extraction; directory traversal (`../`) rejected.
- **Malware Scanning**:
  - ClamAV container integration (`clamd` on port 3310).
  - Status pipeline: `UPLOADED -> SCANNING -> CLEAN / INFECTED / UNAVAILABLE -> PROCESSING -> REVIEW`.
  - Infected files are immediately quarantined, marked with malware signature, and never served for download.
- Verified in tests: `test_spoofed_pdf_rejected_by_magic_bytes`, `test_path_traversal_filename_rejected`, `test_document_pipeline.py`.

## 5. Privacy & Data Protection Controls
- **Aadhaar Data**: Plaintext 12-digit Aadhaar numbers are **never stored** in the database. Aadhaar is normalized and converted to a one-way cryptographic SHA-256 hash (`aadhaar_hash`) solely for deduplication.
- **Bank Account Data**: Account numbers are encrypted at rest using AES-256-GCM (`FIELD_ENCRYPTION_KEY`). Decryption occurs only at point-of-use during approved disbursement preparation.
- **Audit Logging**: All access to sensitive records generates an `AuditLog` entry recording `actor_id`, `actor_role`, `action`, `resource_id`, and client IP.
- **Logging Sanitization**: Production log formatters mask tokens, passwords, and sensitive identifiers.

## 6. AI Governance & Decision Boundary
- **Assistive Scope**: Google Gemini / Vision OCR models are strictly auxiliary:
  - Document quality assessment (blur, glare, resolution).
  - Field extraction suggestion (income amount, certificate date).
  - Cross-document inconsistency flagging (name mismatch, date discrepancies).
- **Hard Decision Boundary**:
  - AI **never** approves, rejects, or decides application eligibility.
  - AI extraction confidence scores and limitations are visible to the scrutiny officer.
  - Every official eligibility decision and status transition is deterministically validated by code and signed off by authorized human officers.

## 7. Secret Management Audit
- Full repository scan conducted across codebase.
- Findings: **0 hardcoded secrets**, 0 private keys, 0 cloud provider credentials.
- `.env.example` provides placeholders only with explicit security warnings.


---

## Phase 13: Production Security Audit & Vulnerability Assessment Matrix

### 1. Systematic Security Review Across 17 Threat Vectors

| Threat Vector | Assessment Result | Technical Mitigation & Architectural Evidence |
| :--- | :--- | :--- |
| **1. SQL Injection** | **PROTECTED** | All queries use SQLAlchemy 2.0 parameterized ORM. Zero raw SQL string interpolation. |
| **2. Cross-Site Scripting (XSS)** | **PROTECTED** | Next.js React 18 JSX auto-escaping; HTTP headers enforce strict `Content-Security-Policy`. |
| **3. Cross-Site Request Forgery (CSRF)**| **PROTECTED** | Session cookies set with `SameSite=Lax/Strict` and `HttpOnly=True`. API routes require explicit `Bearer <JWT>` authorization headers. |
| **4. Server-Side Request Forgery (SSRF)**| **PROTECTED** | External HTTP calls strictly restricted to pre-whitelisted government adapter endpoints. User inputs cannot specify outbound request destinations. |
| **5. Insecure Direct Object References (IDOR)**| **PROTECTED** | Applicant data access validated via `application.applicant_id == current_user.id`. Officer routes enforce role and assigned case scopes. |
| **6. Path Traversal** | **PROTECTED** | All uploads assigned cryptographically generated UUID filenames. User-submitted filenames sanitized; no directory separators allowed. |
| **7. Malicious File Uploads** | **PROTECTED** | Three-tier defense: MIME verification (`python-magic`), file extension whitelisting, and mandatory asynchronous ClamAV virus scanning. |
| **8. Authentication Bypass** | **PROTECTED** | Password hashing via `bcrypt` (12 work rounds); JWT expiration set to 15 minutes; SHA-256 hashed refresh tokens; account lockout after 5 consecutive failed attempts. |
| **9. Authorization Bypass (Privilege Escalation)**| **PROTECTED** | Route-level `require_roles(...)` FastAPI dependencies enforce least-privilege RBAC. Super Admin operations isolated. |
| **10. JWT Misuse & Token Tampering** | **PROTECTED** | Cryptographically signed tokens (HS256); secret key decoupled to environment variable; token expiration explicitly enforced. |
| **11. Replay Attacks** | **PROTECTED** | State transition endpoints require idempotency validation; short-lived access tokens limit token replay window. |
| **12. Rate Abuse & Brute Force** | **PROTECTED** | `FastAPI-Limiter` active on sensitive routes (`/login`, `/register`, `/documents/upload`, `/verify`). |
| **13. Mass Assignment Vulnerabilities** | **PROTECTED** | Pydantic v2 schemas enforce strict input contracts. Disallowed fields silently ignored or rejected with 422 Unprocessable Entity. |
| **14. Secret Leakage** | **PROTECTED** | Zero production secrets in Git. `.gitignore` protects `.env` files; CI pipeline runs automated `detect-secrets` checks. |
| **15. PII Leakage & Aadhaar Exposure** | **PROTECTED** | Raw 12-digit Aadhaar numbers are never stored (one-way SHA-256 hash used solely for de-duplication). Bank account numbers and mobile numbers encrypted via Fernet AES-256. |
| **16. Dependency Vulnerabilities** | **PROTECTED** | Automated dependency audits in CI: `pip-audit` for Python and `npm audit` for Node.js dependencies. |
| **17. Container Weaknesses** | **PROTECTED** | Production Dockerfiles run as dedicated non-root user `mota` (UID 1001); slim base images; unnecessary build tooling discarded via multi-stage builds. |

---

### 2. Production Readiness Scorecard

| Area | Status | Evidence & Verification Reference |
| :--- | :--- | :--- |
| **Architecture** | `READY` | Decoupled multi-tier architecture, documented trust boundaries in `ARCHITECTURE.md`. |
| **Security** | `READY` | 17-point security review passed; PII encryption; zero secrets in Git repository. |
| **Authentication** | `READY` | Bcrypt hashing, 15-min JWT, token revocation, account lockout verified in test suite. |
| **Authorization** | `READY` | 6-role RBAC verified; admin routes protected against applicant access. |
| **Database** | `READY` | 4 versioned migrations, production indexing migration `0004_production_indexes.py`. |
| **Storage** | `READY` | `StorageService` abstraction; protected file access; UUID key isolation. |
| **AI Governance** | `READY WITH CONDITIONS`| Strict assistive boundary; deterministic eligibility; cloud model requires institutional API key. |
| **OCR Abstraction** | `READY` | Pluggable OCR interface; advisory text extraction; human verification mandatory. |
| **Government Integrations** | `READY WITH CONDITIONS`| Adapters architected; all operate in honest `STUB` mode; requires official MoU and credentials. |
| **Backup Strategy** | `READY` | Documented in `BACKUP_RECOVERY.md`; pg_dump/pg_restore procedures verified. |
| **Recovery Strategy** | `READY` | Disaster recovery runbook documented; database rebuild from migrations verified. |
| **Observability** | `READY WITH CONDITIONS`| Structured JSON logs, `/health` endpoint ready; Prometheus/Grafana requires institutional config. |
| **CI/CD Automation** | `READY` | Full GitHub Actions pipeline (`.github/workflows/ci.yml`) with lint, test, audit, and build. |
| **Documentation** | `READY` | Complete suite: Runbook, Institutional Handover, Data Governance, AI Governance, Limitations. |
| **Data Governance** | `READY` | 7-category data classification; DPDPA compliance alignment; raw Aadhaar zero-storage. |
| **Operational Readiness**| `READY WITH CONDITIONS`| Operational runbooks complete; live deployment requires institutional infrastructure allocation. |

**OVERALL READINESS: `READY WITH CONDITIONS`**  
*(Deployment to live institutional operation requires formal agency credentials and sovereign hosting environment).*
