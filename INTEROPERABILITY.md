# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Enterprise Interoperability & Integration Architecture Specification

> **Classification:** Enterprise Interoperability Specification  
> **Status:** APPROVED BASELINE (Phase 17)  
> **Core Mandate:** Secure System Integration Without Privacy, Eligibility, or Audit Compromise

---

## 1. Interoperability Architecture & Boundary Model

```text
                             +──────────────────────────────────────+
                             │ Authorized External Institutional    │
                             │ Gateways (NIC / NSP / State Portals) │
                             +──────────────────┬───────────────────+
                                                │
                                                │ mTLS (TLS 1.3) / OAuth2
                                                ▼
                             ┌──────────────────────────────────────┐
                             │ Institutional Ingress & API Gateway   │
                             │ - Rate Limiting & Quota Management   │
                             │ - Signature Verification (HMAC-SHA256)│
                             │ - WAF & Threat Filter                │
                             └──────────────────┬───────────────────┘
                                                │
                         ┌──────────────────────┴──────────────────────┐
                         │                                             │
                         ▼                                             ▼
                 REST API Services                             Event / Webhooks
              (/api/v1/ institutional)                     (HMAC Signature Verified)
                         │                                             │
                         └──────────────────────┬──────────────────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │ FastAPI Core Platform │
                                    └───────────┬───────────┘
                                                │
                        ┌───────────────────────┼───────────────────────┐
                        │                       │                       │
                        ▼                       ▼                       ▼
               ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
               │ PostgreSQL 16  │      │ Redis 7 Broker │      │ Celery Workers │
               │ (ACID & Audit) │      │ (Queue & Cache)│      │ (I/O & Scans)  │
               └────────────────┘      └────────────────┘      └────────────────┘
```

---

## 2. API Categorization & Access Boundaries

1. **Internal Client APIs (`/api/v1/auth`, `/api/v1/applicant`, `/api/v1/applications`):**
   - Consumed exclusively by the official Next.js web application.
   - Enforces user session JWT tokens and CSRF protection.
2. **Operational Officer & Admin APIs (`/api/v1/admin/*`, `/api/v1/cases/*`):**
   - Restricted to authenticated scrutiny officers and administrators via role scoping.
3. **Authorized Institutional APIs (`/api/v1/schemes`, `/api/v1/external/*`):**
   - Designed for inter-agency coordination (State Tribal Welfare Directorates, Central Scholarship Repositories).
   - Requires mutual TLS (mTLS) or OAuth2 client credentials with strict field filtering.
4. **Government Integration Adapters (`UIDAI`, `DigiLocker`, `NSP`, `DBT`, `MoTA`):**
   - Outbound integration adapters implementing the `BaseIntegrationAdapter` interface.
   - Reside safely behind institutional authorization gates.

---

## 3. Secure Webhook Framework Specification

When inbound or outbound webhooks are commissioned with authorized institutional partners:
- **Signature Algorithm:** Every webhook payload must be signed using `HMAC-SHA256` with a pre-shared institutional secret.
- **Signature Header:** `X-MoTA-Signature: t=<timestamp>,v1=<hex_signature>`.
- **Replay Protection:** Webhooks with a timestamp differing by more than **300 seconds** from server time are rejected immediately.
- **Idempotency:** Webhook deliveries must include an `X-Event-ID` header; duplicate event IDs are processed idempotently.
- **Payload Validation:** Inbound payloads are strictly validated against Pydantic schemas before processing.

---

## 4. Platform Event Catalog

The platform defines standard internal domain events for asynchronous decoupling:

| Event Name | Trigger Condition | Emitting Subsystem | Payload Scope (Minimized PII) |
| :--- | :--- | :--- | :--- |
| **`ApplicationSubmitted`** | Applicant completes submission | Application Service | `application_id`, `scheme_code`, `timestamp` |
| **`ApplicationStatusChanged`**| Officer updates application state | Case Management | `application_id`, `old_status`, `new_status`, `actor_id` |
| **`DocumentUploaded`** | Applicant uploads certificate | Document Service | `document_id`, `application_id`, `doc_type` |
| **`DocumentProcessed`** | ClamAV / OCR pipeline finishes | Worker Pipeline | `document_id`, `scan_status`, `ocr_confidence` |
| **`DeficiencyCreated`** | Scrutiny officer issues deficiency | Scrutiny Workbench | `deficiency_id`, `application_id`, `remarks_hash` |
| **`DeficiencyResolved`** | Applicant re-uploads document | Application Service | `deficiency_id`, `application_id`, `resubmitted_at` |
| **`CaseAssigned`** | Application routed to officer | Work Queue Service | `application_id`, `officer_id`, `assigned_by` |
| **`GovVerificationUpdated`**| Government adapter execution | Integration Gateway | `application_id`, `adapter_name`, `status` |
| **`NotificationCreated`** | System triggers alert | Notification Service | `notification_id`, `user_id`, `channel` |

---

## 5. Safe Degraded Mode & Failure Isolation

- **Circuit Breaker:** Outbound calls to external gateways employ circuit breakers (`CLOSED` → `OPEN` after 5 consecutive timeouts → `HALF-OPEN` after 60s cooldown).
- **Graceful Degradation:** An external integration failure never crashes the application server or prevents application submissions.
- **Zero False Approvals:** A timed-out or failed verification request explicitly returns `REQUIRES_AUTHORIZED_ACCESS` or `PENDING`. **Never marks an unverified record as verified.**
