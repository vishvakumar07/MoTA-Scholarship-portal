# User Acceptance Testing (UAT) Report
## MoTA Scholarship & Fellowship Management System — Phase 12

**Test Date:** 2026-09-27
**Environment:** Development / Local Docker
**Tester Role:** Phase 12 QA Engineer (automated + manual)
**Status:** PILOT READINESS VALIDATED

---

## 1. UAT Scope

UAT covers all primary user journeys across all three roles implemented in the system.

---

## 2. Applicant Journey Tests

| # | Test Case | Expected | Result | Notes |
|---|-----------|----------|--------|-------|
| A-01 | Applicant registers with valid details | Registration succeeds, JWT token returned | PASS | |
| A-02 | Applicant logs in with correct credentials | 200 OK, token issued | PASS | |
| A-03 | Applicant logs in with wrong password | 401 Unauthorized | PASS | |
| A-04 | Applicant views scheme catalogue | List of active schemes returned | PASS | |
| A-05 | Applicant checks eligibility for scheme | Eligibility result with rule details | PASS | Deterministic rule engine |
| A-06 | Applicant submits application | Application created, status = DRAFT | PASS | |
| A-07 | Applicant uploads supporting document | Document stored, scan queued | PASS | |
| A-08 | Applicant views application status | Status and timeline returned | PASS | |
| A-09 | Applicant receives deficiency notice | Notification stored and retrievable | PASS | Delivery = STUB |
| A-10 | Applicant resubmits after deficiency | Application moves to RESUBMITTED | PASS | |

---

## 3. Officer Journey Tests

| # | Test Case | Expected | Result | Notes |
|---|-----------|----------|--------|-------|
| O-01 | Officer logs in | 200 OK, officer role token | PASS | |
| O-02 | Officer views assigned applications | List filtered by assignment | PASS | |
| O-03 | Officer opens application for scrutiny | Full application + documents visible | PASS | |
| O-04 | Officer raises deficiency notice | Deficiency created, applicant notified | PASS | Notification = STUB |
| O-05 | Officer approves documents | Document status updated | PASS | |
| O-06 | Officer recommends for approval | Application status = RECOMMENDED | PASS | |
| O-07 | Officer rejects application | Application status = REJECTED, reason recorded | PASS | |
| O-08 | Officer views audit trail | All actions logged in audit table | PASS | |

---

## 4. Admin Journey Tests

| # | Test Case | Expected | Result | Notes |
|---|-----------|----------|--------|-------|
| ADM-01 | Admin logs in | 200 OK, admin role token | PASS | |
| ADM-02 | Admin creates scheme | New scheme created with DRAFT status | PASS | |
| ADM-03 | Admin publishes scheme version | Version status = PUBLISHED | PASS | |
| ADM-04 | Admin adds eligibility rules | Rules stored with official source references | PASS | |
| ADM-05 | Admin views analytics dashboard | Application counts, status distribution | PASS | |
| ADM-06 | Admin exports audit log | Audit records retrievable | PASS | |
| ADM-07 | Admin manages user roles | Role assignment via RBAC | PASS | |

---

## 5. System / Security Tests

| # | Test Case | Expected | Result | Notes |
|---|-----------|----------|--------|-------|
| SEC-01 | Access protected endpoint without token | 401 Unauthorized | PASS | |
| SEC-02 | Access admin endpoint as applicant | 403 Forbidden | PASS | RBAC enforced |
| SEC-03 | Upload file > max size | 413 / validation error | PASS | |
| SEC-04 | Upload non-whitelisted file type | 422 / rejected | PASS | |
| SEC-05 | Rate limiting on auth endpoints | 429 after threshold | PASS | |
| SEC-06 | Audit log entry created for every state change | Audit record present | PASS | |
| SEC-07 | Aadhaar number not stored in plaintext | Only SHA-256 hash in DB | PASS | Verified by schema |
| SEC-08 | Government integration stubs return correct status | Status = STUB_NOT_CONFIGURED | PASS | Truthfulness rule |

---

## 6. Performance Validation (from perf_benchmark.py)

| Metric | Result | Threshold | Status |
|--------|--------|-----------|--------|
| /health avg latency | 90.2 ms | < 200 ms | PASS |
| /api/v1/schemes avg latency | 3.77 ms | < 50 ms | PASS |
| Rule engine eval (2-rule) | 25.45 us | < 1 ms | PASS |
| Storage write 100 KB | 0.18 ms | < 10 ms | PASS |
| JWT encode+decode | 89.39 us | < 500 us | PASS |
| Aadhaar SHA-256 hash | 0.88 us | < 10 us | PASS |

---

## 7. UAT Summary

| Category | Total Tests | Passed | Failed | Blocked |
|----------|------------|--------|--------|---------|
| Applicant Journey | 10 | 10 | 0 | 0 |
| Officer Journey | 8 | 8 | 0 | 0 |
| Admin Journey | 7 | 7 | 0 | 0 |
| Security | 8 | 8 | 0 | 0 |
| Performance | 6 | 6 | 0 | 0 |
| **TOTAL** | **39** | **39** | **0** | **0** |

---

## 8. Known Limitations Accepted for Pilot

| Item | Limitation | Impact |
|------|-----------|--------|
| Email/SMS delivery | Stub only — no live gateway | Demo notification flow only |
| Aadhaar/DigiLocker | Stub only — no live API | Identity verification manual |
| NSP/PFMS/DBT | Stub only | Disbursement simulated |
| ClamAV | Requires Docker; signatures need regular update | |
| Single-node | No horizontal scaling in dev build | Demo/pilot scale only |

All limitations are clearly displayed in the UI and documented.

---

## 9. Pilot Readiness Verdict

**SYSTEM IS PILOT-READY** for controlled demonstration and evaluation.

All 39 UAT test cases pass. All 6 performance metrics pass. Security controls validated. No blocking defects.

---

*UAT Report v1.0 — MoTA Scholarship System — Phase 12*
