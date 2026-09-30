# MoTA AI-Enabled Scholarship and Fellowship Management System
## System Architecture — v2.0 (Revised: Local-First)

**Ministry:** Ministry of Tribal Affairs (MoTA), Government of India  
**Context:** Smart India Hackathon Prototype  
**Version:** 2.0 | **Revised:** 2026-09-23

---

## Core Architectural Principle

```
OFFICIAL DATA FIRST → CONFIGURABLE SCHEME ENGINE →
LOCAL-FIRST APPLICATION → OPTIONAL AI →
OPTIONAL GOVERNMENT INTEGRATIONS → OPTIONAL CLOUD
```

This is a **local-first, Docker-first** prototype.  
No AWS account, no paid cloud service, no paid AI API is required to run the system.

---

## Quick Start

```bash
cp .env.example .env          # Edit: set passwords and secrets
docker compose up --build     # Start all services

# In another terminal:
docker compose exec api alembic upgrade head          # Run migrations
docker compose exec api python infra/scripts/seed_schemes.py  # Seed real scheme data

# Application:
#   Frontend: http://localhost:3000
#   API docs: http://localhost:8000/docs
```

---

## Schemes (Official Source: tribal.nic.in)

All scheme rules sourced from https://tribal.nic.in/ScholarshiP.aspx

| Code | Scheme | Type | Income Limit |
|------|--------|------|-------------|
| PRE_MATRIC | Pre-Matric Scholarship (Class IX–X) | CSS | ≤ Rs. 2.50L/yr |
| POST_MATRIC | Post-Matric Scholarship | CSS | ≤ Rs. 2.50L/yr |
| TOP_CLASS | National Scholarship — Top Class (265 institutes) | Central Sector | ≤ Rs. 6.00L/yr |
| NFS | National Fellowship — MPhil/PhD (750 seats/yr) | Central Sector | — |
| NOS | National Overseas Scholarship | Central Sector | — |

---

## Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Next.js 14 + React 18 + TypeScript | |
| Styling | Tailwind CSS + shadcn/ui | |
| Backend | FastAPI (Python 3.11+) | |
| ORM | SQLAlchemy 2.0 + Alembic | |
| Database | PostgreSQL 15 + pgvector | Via Docker |
| Task Queue | Celery + Redis | Via Docker |
| Storage | Local filesystem (default) | S3-compatible optional |
| AI | Google Gemini (optional) | MockAI when no key |
| OCR | Google Cloud Vision (optional) | Unavailable mode when no key |
| Malware | ClamAV (Docker) | Graceful degradation |
| Containerization | Docker Compose | 6 services |

---

## Service Architecture (Docker Compose)

```
Browser → Next.js :3000 → FastAPI :8000 → PostgreSQL :5432
                                        → Redis :6379 → Celery Worker
                                        → Local Storage (./storage/)
                                        → ClamAV :3310 (optional)

Optional (if API keys configured):
FastAPI → Google Gemini API (AI)
        → Google Cloud Vision API (OCR)
```

**6 Docker services:** `web`, `api`, `worker`, `postgres`, `redis`, `clamav`

---

## Key Service Abstractions

### StorageService
```
LocalStorageService  ← DEFAULT (local filesystem)
S3StorageService     ← OPTIONAL (when STORAGE_PROVIDER=s3)
```

### AIService
```
GeminiAIService   ← when GOOGLE_AI_API_KEY is set
MockAIService     ← DEFAULT (shows "AI unavailable" status)
```

### OCRService
```
GoogleVisionOCR   ← when GOOGLE_CLOUD_VISION_API_KEY is set
UnavailableOCR    ← DEFAULT (shows "manual review required")
```

### GovernmentIntegrationService
```
StubAdapter (all)  ← DEFAULT (shows "integration required" status)
LiveAdapter        ← when authorized credentials are provided
```

All business logic uses only the abstract interface. Switching providers requires only a config change.

---

## Application State Machine (17 States)

```
DRAFT → SUBMITTED → DOCUMENT_PROCESSING → DOCUMENT_VERIFICATION
    → DEFICIENCY ↔ RESUBMITTED
    → ELIGIBILITY_REVIEW → ELIGIBLE / INELIGIBLE
    → SCRUTINY → SHORTLISTED
    → SELECTION_REVIEW → SELECTED / NOT_SELECTED
    → POST_SELECTION → COMPLETED
WITHDRAWN (from most states)
```
All states configurable per scheme via `scheme_workflows` table.

---

## 6 Roles (RBAC)

`applicant` · `verification_officer` · `scrutiny_officer` ·  
`selection_committee` · `scheme_admin` · `super_admin`

---

## Database Schema (25+ Entities)

Identity: `users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `refresh_tokens`  
Applicant: `applicant_profiles`, `applicant_education`  
Schemes: `schemes`, `scheme_versions`, `scheme_rules`, `scheme_documents`, `scheme_form_fields`, `scheme_workflows`, `scheme_selection_criteria`  
Applications: `applications`, `application_answers`, `application_status_history`  
Documents: `documents`, `document_extracted_fields`, `document_verification_results`  
Workflow: `eligibility_results`, `deficiencies`, `selection_results`  
System: `notifications`, `audit_logs`, `knowledge_documents`, `knowledge_chunks`, `ai_analysis_results`

---

## AI Cost Controls

- AI called ONLY when a document is uploaded (once, async via Celery)
- Results cached in `ai_analysis_results` table — same document never reprocessed
- AI NOT called on: page loads, status queries, dashboard views, browsing
- Application fully functional without any AI API key

---

## Data Principles

| Type | Rule |
|------|------|
| Aadhaar numbers | SHA-256 hash only — never store plaintext |
| Bank account numbers | AES-256-GCM encrypted at column level |
| Document files | Private storage; signed access URLs (15-min TTL) |
| Audit logs | Append-only; DB trigger prevents deletion |
| Scheme rules | Versioned; applications locked to version at submission |
| Government statistics | Shown only with source + date attribution |
| Demo/test records | Clearly marked `DEMO`; never presented as real |
| Fabricated applicants | **PROHIBITED** |

---

## Environment Variables

### Required (app won't start without these)
`DATABASE_URL`, `POSTGRES_PASSWORD`, `REDIS_URL`,  
`JWT_SECRET_KEY`, `FIELD_ENCRYPTION_KEY`

### Optional — AI
`GOOGLE_AI_API_KEY`, `GOOGLE_CLOUD_VISION_API_KEY`

### Optional — Storage (when STORAGE_PROVIDER=s3)
`S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`

### Optional — Notifications
`SMTP_*` variables, `SMS_*` variables

### Optional — Government Integrations
Per-integration credentials (all stubs by default)

See `.env.example` for full documentation.

---

## What Is NOT Required

- AWS account ✗
- S3 bucket ✗  
- RDS / managed PostgreSQL ✗
- Pinecone / Weaviate / paid vector database ✗
- VirusTotal / paid malware scanning ✗
- Kubernetes ✗
- Load balancer ✗
- CDN ✗
- Government API credentials ✗ (stubs used by default)
- AI API key ✗ (mock mode available)

---

## Future Optional Cloud Path

If cloud deployment is needed later:
1. Set `STORAGE_PROVIDER=s3` + S3 credentials → switches to S3 automatically
2. Point `DATABASE_URL` to managed PostgreSQL → no code change
3. Configure managed Redis → change `REDIS_URL`
4. Add `GOOGLE_AI_API_KEY` → switches from mock to real AI

No code changes required — only environment configuration.

---

*Source for scheme data: https://tribal.nic.in/ScholarshiP.aspx (live, 2026-09-23)*  
*Full implementation plan: See implementation_plan.md artifact*


---

## Phase 11 System Architecture Diagram

```text
Applicant / Officer / Admin
            |
            v
     Next.js 14 Web
     (Port 3000)
            |
            v  REST / JSON (JWT Auth)
     FastAPI Backend
     (Port 8000)
            |
    +-------+-------------------------+
    |                                 |
    v                                 v
PostgreSQL 15                       Redis 7
(Local Relational DB)                 |
    |                                 v
    |                            Celery Worker
    |                                 |
    |                                 v
    |                          AI/OCR Pipeline
    |                          (Assistive Gemini / Vision / Mock)
    |
    +--> Eligibility Engine (Deterministic & Explainable)
    +--> Application Engine (Scheme Version Locked)
    +--> Case Management (Officer Work Queue & Notes)
    +--> Notifications (In-App, Multi-Channel)
    +--> Analytics (Database-Derived Operational Metrics)
    +--> Audit Logs (Immutable Event Ledger)
    +--> Government Adapters (UIDAI, DigiLocker, NSP, DBT, MoTA Stubs)
    |
    v
Local File Storage (storage/documents/)
    |
    v
ClamAV Anti-Malware Service (Port 3310)
```

### Component Responsibilities & Boundaries:
1. **Next.js Web**: Accessible, responsive citizen & officer portal with client-side state handling and zero secret leakage.
2. **FastAPI Backend**: High-performance async REST API providing strictly typed schemas, RBAC, IDOR protection, and rate limiting.
3. **PostgreSQL**: Stores relational data, versioned scheme rules, encrypted bank details, hashed Aadhaar records, and immutable audit logs.
4. **Redis + Celery**: Manages asynchronous document scanning and AI/OCR pipelines without blocking citizen requests.
5. **ClamAV**: Validates uploaded files for malicious code before passing to downstream processors.
6. **Government Integration Adapters**: Strictly isolated abstraction layer exposing real configuration states without simulating live credentials.


---

## Phase 13: Production Architecture & Institutional Deployment Model

### 1. Pilot vs. Production Architecture Comparison

| Dimension | Pilot / Demo Architecture | Future Production Architecture |
| :--- | :--- | :--- |
| **Topology** | Single-node Docker Compose | Multi-node sovereign cluster (Kubernetes / HA Docker) |
| **Ingress & TLS** | Direct port mapping (3000, 8000), HTTP local | Institutional Reverse Proxy / WAF, TLS 1.3 Termination |
| **Database** | Single PostgreSQL container with volume mount | Managed PostgreSQL HA cluster with read replicas & WAL archiving |
| **Storage** | Local filesystem (`apps/api/storage/uploads`) | Sovereign S3-compatible object store with immutable audit bucket |
| **Task Queue** | Single Redis instance, single Celery worker | Redis Sentinel/Cluster, autoscaling multi-queue worker pool |
| **Secrets** | Local `.env` file | Vault / KMS / Sovereign Secret Manager injection |
| **Government Gateways** | Mock / Stub adapters (`REQUIRES_AUTHORIZED_ACCESS`) | Authenticated mTLS / OAuth2 government gateways via secure NIC tunnel |
| **High Availability** | None (Single host failover) | Multi-AZ / Multi-datacenter high availability |

### 2. Production Network Topology & Trust Boundaries

```text
======================= PUBLIC UNTRUSTED NETWORK =======================
                                    │
                                    │ HTTPS (TLS 1.3, Port 443)
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│ [TRUST BOUNDARY 1: PERIMETER]                                        │
│ Institutional Reverse Proxy / Load Balancer / WAF                     │
│ - SSL/TLS Termination                                                 │
│ - Volumetric DDoS Mitigation                                          │
│ - Web Application Firewall (WAF) Inspection                           │
│ - Rate Limiting (IP-level)                                            │
└───────────────────┬───────────────────────────────┬───────────────────┘
                    │                               │
       Internal HTTP│                               │Internal HTTP
       (Port 3000)  │                               │(Port 8000)
                    ▼                               ▼
┌───────────────────────────────┐ ┌─────────────────────────────────────┐
│ [TRUST BOUNDARY 2: DMZ]       │ │ [TRUST BOUNDARY 2: DMZ]             │
│ Next.js Frontend (Node.js)    │ │ FastAPI Application Server (Gunicorn)│
│ - Static Asset Delivery       │ │ - JWT Authentication & RBAC Guard   │
│ - SSR Dynamic Pages           │ │ - Pydantic Request Validation       │
│ - Non-Root Container (nextjs) │ │ - Non-Root Container (mota:1001)    │
└───────────────────────────────┘ └───────┬───────────────┬─────────────┘
                                          │               │
                                   Private│        Private│
                                    TCP   │         TCP   │
                                          ▼               ▼
┌──────────────────────────────────────────────────┐ ┌──────────────────┐
│ [TRUST BOUNDARY 3: PRIVATE SERVICES NETWORK]     │ │ ClamAV Antivirus │
│ Redis 7 (Protected by Strong AUTH Password)      │ │ Daemon (TCP 3310)│
│ - Celery Task Broker                             │ │ - Internal scan  │
│ - Rate Limit State Cache                         │ │ - Isolated sandbox
└─────────────────────────┬────────────────────────┘ └──────────────────┘
                          │
                          │ Task Dispatch
                          ▼
┌──────────────────────────────────────────────────┐
│ Celery Asynchronous Workers (mota:1001)          │
│ - Document Malware Scan Dispatch                 │
│ - OCR & AI Assistive Extractions                 │
│ - Notification Dispatch (Email / SMS)            │
│ - Scheduled Analytics Rollups                    │
└─────────────────────────┬────────────────────────┘
                          │
                          │ SQL Queries (Connection Pool, Port 5432)
                          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ [TRUST BOUNDARY 4: SECURE DATA ISOLATION ZONE]                        │
│ PostgreSQL 16 Cluster + pgvector                                      │
│ - Restricted database user (`mota_app_user`)                          │
│ - Encrypted Tablespaces (Storage at rest)                             │
│ - Field-Level Encryption (AES-256 Fernet for PII)                     │
│ - Immutable Append-Only Audit Logs                                    │
└───────────────────────────────────────────────────────────────────────┘
```

### 3. Production Data Flow Diagram

```text
[Applicant Browser]
        │
        │ 1. Submit Application + Encrypted PII Payload (HTTPS)
        ▼
[FastAPI Gateway]
        │
        ├─ 2. Evaluate Eligibility ──> [Deterministic Scheme Rule Engine] (100% Deterministic)
        │
        ├─ 3. Write Application Record ─> [PostgreSQL DB] (Field-level encrypted bank/Aadhaar hash)
        │
        ├─ 4. Stream Uploaded Document ─> [StorageService] (UUID sanitized filename)
        │
        └─ 5. Enqueue Document Scan ───> [Redis Queue]
                                                │
                                                ▼
                                    [Celery Background Worker]
                                                │
                                                ├─ 6. Antivirus Scan ──> [ClamAV Daemon]
                                                │
                                                ├─ 7. Advisory OCR ────> [OCR / AIService] (Advisory Only)
                                                │
                                                └─ 8. Update Status ───> [PostgreSQL DB] (Scrutiny Ready)
                                                                                │
                                                                                ▼
                                                                [Officer Scrutiny Workbench]
```

### 4. Zero-Downtime & High Availability Status
- **Current State:** `NOT CONFIGURED`.
- **Institutional Implementation Requirement:** Blue-Green or Rolling deployment orchestrations must be configured at the institutional ingress controller level before claiming 99.99% availability.
