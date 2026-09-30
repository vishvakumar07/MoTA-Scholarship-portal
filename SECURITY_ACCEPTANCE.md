# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Security Acceptance & Technical Verification Matrix

> **Classification:** Security Engineering & Pre-Deployment Acceptance  
> **Status:** ACCEPTED FOR CONTROLLED PILOT / PRE-PRODUCTION STAGING  
> **Overall Assessment:** ZERO CRITICAL VULNERABILITIES DETECTED  
> **Formal Audit Notice:** Third-party CERT-In empanelled VAPT certification: `PENDING FORMAL INSTITUTIONAL ENGAGEMENT`.

---

## 1. Security Architecture & Controls Summary

| Security Domain | Architectural Control | Verification Method | Result |
| :--- | :--- | :--- | :--- |
| **Authentication** | Password hashing via `bcrypt` (12 rounds); 15-min JWT access tokens; SHA-256 refresh tokens; account lockout after 5 failed attempts. | Automated unit & integration tests (`test_phase8_hardening.py`) | **PASSED** |
| **Authorization (RBAC)** | Strict role enforcement across 6 roles (`applicant`, `verification_officer`, `scrutiny_officer`, `selection_committee`, `scheme_admin`, `super_admin`). | Test suite verifying 403 Forbidden on unprivileged access | **PASSED** |
| **Data Protection at Rest** | Field-level encryption (Fernet AES-256) for PII (bank accounts, mobile numbers); raw 12-digit Aadhaar **NEVER stored** (one-way SHA-256 hash only). | Schema & model verification (`models/application.py`, `models/user.py`) | **PASSED** |
| **Data Protection in Transit**| Enforced HTTPS / TLS 1.3 configuration templates; `Secure` and `HttpOnly` cookie flags; strict CORS. | Configuration audit (`config.py`, `main.py`) | **PASSED** |
| **Injection Defense** | 100% SQLAlchemy 2.0 parameterized queries; React 18 JSX auto-escaping; strict Pydantic v2 input schema validation. | Static analysis and test suite execution | **PASSED** |
| **IDOR Protection** | Route-level ownership checks (`application.applicant_id == current_user.id`); officer case scoping. | Automated IDOR attack simulation tests (`test_phase8_hardening.py`, `test_phase9_cases_and_notifications.py`) | **PASSED** |
| **File Upload Security** | MIME type sniffing (`python-magic`), extension whitelisting, UUID storage keys, ClamAV antivirus scanning. | Malformed file and path traversal test suite (`test_document_pipeline.py`) | **PASSED** |
| **Rate Limiting & DoS** | Sliding-window in-memory & Redis rate limiting on auth, registration, upload, and verification routes. | Rate limiter threshold stress tests | **PASSED** |
| **Audit & Accountability** | Append-only `AuditLog` table capturing actor, action, entity, IP, and timestamp. Zero update/delete routes. | Audit generation test suite (`test_audit_and_security.py`) | **PASSED** |

---

## 2. Specific Attack Vector Test Results

| Attack Vector | Simulated Scenario | System Response | Acceptance Status |
| :--- | :--- | :--- | :--- |
| **SQL Injection** | Injected `' OR 1=1 --` into login, application search, and scheme query parameters. | Handled safely by ORM parameters; zero syntax execution. | **ACCEPTED** |
| **XSS** | Injected `<script>alert(1)</script>` into applicant personal statements and address fields. | Automatically escaped by Next.js frontend; displayed as inert string. | **ACCEPTED** |
| **CSRF** | Cross-origin request forgery simulation without Bearer token. | Rejected immediately with `401 Unauthorized`. | **ACCEPTED** |
| **IDOR (Application)** | Applicant A attempted fetching `/api/v1/applications/{id}` belonging to Applicant B. | Rejected with `404 Not Found` / `403 Forbidden`. | **ACCEPTED** |
| **IDOR (Timeline)** | Applicant attempted inspecting internal officer timeline notes. | Internal officer events stripped from response. | **ACCEPTED** |
| **Path Traversal** | Uploaded file with name `../../../../etc/passwd.pdf`. | Path stripped; file saved as `{uuid4}.pdf`. | **ACCEPTED** |
| **MIME Spoofing** | Executable `.exe` renamed to `.pdf` with invalid magic bytes. | Rejected with `400 Bad Request: Invalid MIME type`. | **ACCEPTED** |
| **Expired Token** | Request made with JWT timestamp expired by 1 second. | Rejected with `401 Unauthorized: Token has expired`. | **ACCEPTED** |
| **Privilege Escalation**| Applicant token submitted to `/api/v1/admin/schemes`. | Rejected with `403 Forbidden: Insufficient role permissions`. | **ACCEPTED** |
| **Credential Leakage** | Automated scan of repository files via `detect-secrets` and regex pattern search. | Zero production secrets or private keys in repository. | **ACCEPTED** |

---

## 3. Residual Risks & Production Requirements

1. **Host Environment Allocation:** System is currently validated on local test host. Final production launch requires deployment to sovereign government infrastructure (e.g., NIC MeghRaj / State Data Centre).
2. **CERT-In Audit:** Formal third-party empanelled CERT-In audit certification is required prior to public go-live (`PENDING FORMAL INSTITUTIONAL ENGAGEMENT`).
3. **WAF Deployment:** Edge network layer DDoS mitigation and IP reputation filtering must be enabled at institutional reverse proxy/WAF.

---

## 4. Final Security Acceptance Verdict

### Status: **`ACCEPTED FOR STAGING / PRE-PRODUCTION PILOT`**
*(Production deployment blocked pending sovereign host allocation and formal CERT-In audit clearance).*
