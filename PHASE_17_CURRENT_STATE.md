# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Phase 17 Current-State Interoperability & Integration Assessment

> **Classification:** Enterprise Interoperability Assessment  
> **Evaluation Date:** September 2026  
> **Baseline Version:** Version `1.0.0-pilot`  
> **Mandate:** Zero-Fabrication, Strict External Boundaries, Deterministic Authority

---

## 1. Existing Interoperability Capabilities

- **RESTful API Surface:** 59 endpoints implemented across 11 modular routers under `/api/v1/` prefix.
- **Authentication & Authorization:** JWT Bearer token authentication (15-min expiry), SHA-256 hashed refresh tokens, and 6-role RBAC scope enforcement.
- **Data Exchange Format:** Standard JSON request and response envelopes with strict Pydantic v2 schemas.
- **Correlation Tracking:** Correlation IDs (`X-Request-ID`) generated per request and propagated through application headers and structured JSON logs.
- **Document Streaming:** Gated document download endpoint (`GET /api/v1/documents/{document_id}/download`) with role and ownership verification.
- **Analytics Export:** Privacy-preserving aggregated CSV export (`GET /api/v1/admin/analytics/export`) for authorized officers and administrators.

---

## 2. Existing External Integrations & Gated Boundaries

| Integration Interface | Subsystem | Current State | Operational Mode | Evidence & Boundary |
| :--- | :--- | :--- | :--- | :--- |
| **UIDAI (Aadhaar)** | Identity Verification | `STUB` | Honest Advisory | Returns `REQUIRES_AUTHORIZED_ACCESS`; zero fake tokens ([adapters.py](file:///E:/MoTA%20Scholarship/apps/api/integrations/adapters.py)) |
| **DigiLocker** | Certificate Fetch | `STUB` | Honest Advisory | Returns `REQUIRES_AUTHORIZED_ACCESS`; zero fake documents |
| **NSP** | Benefit De-duplication | `STUB` | Honest Advisory | Returns `REQUIRES_AUTHORIZED_ACCESS`; zero cross-portal records |
| **DBT / PFMS** | Electronic Sanction | `STUB` | Honest Advisory | Returns `REQUIRES_AUTHORIZED_ACCESS`; zero fake UTRs |
| **MoTA Central** | Scholar Registry | `STUB` | Honest Advisory | Returns `REQUIRES_AUTHORIZED_ACCESS`; legacy database reconciliation |
| **AI Document Intelligence** | Google Gemini API | `CONFIGURED` | Advisory MOCK | Default: `MOCK`; Cloud Gemini ready upon `GEMINI_API_KEY` configuration |
| **Malware Scanning** | ClamAV Daemon | `CONFIGURED` | Real-time TCP | Mandatorily scans before scrutiny; isolates infected streams |
| **Notifications** | SMTP Relay / SMS | `CONFIGURED` | Database In-App | In-app notification active; SMTP/SMS in simulated delivery mode |

---

## 3. Current Interoperability Limitations

1. **Government Integration Gate:** All 5 adapters remain strictly in `STUB` mode pending formal bilateral institutional MoUs and credentials.
2. **External Institutional Webhooks:** Inbound webhooks from third-party university/banking portals are `NOT CONFIGURED` until institutional signing keys are allocated.
3. **Identity Federation:** OpenID Connect (OIDC) / Jan Parichay SSO is architected as an abstraction but unactivated pending sovereign IdP onboarding.
4. **Bulk Exchange:** Unrestricted public bulk export is prohibited; only authenticated role-scoped operational exports are permitted.
