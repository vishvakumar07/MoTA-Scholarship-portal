# MoTA AI-Enabled Scholarship & Fellowship Management System

**Ministry of Tribal Affairs (MoTA), Government of India**  
*Smart India Hackathon Prototype*  
*Version 2.0 (Local-First)*

---

## Overview

An end-to-end digital platform for administering Ministry of Tribal Affairs (MoTA) scholarship and fellowship schemes for Scheduled Tribe students across India.

### Key Highlights
- **Official Data First:** All 5 core MoTA schemes (`PRE_MATRIC`, `POST_MATRIC`, `TOP_CLASS`, `NFS`, `NOS`) seeded with verified rules and source metadata from [tribal.nic.in/ScholarshiP.aspx](https://tribal.nic.in/ScholarshiP.aspx).
- **Local-First Architecture:** Runs 100% locally on standard developer hardware. No AWS account, paid cloud, or third-party paid subscriptions required.
- **Configurable Scheme Engine:** Dynamic eligibility rules, form fields, documents, and 17-state application workflows.
- **Optional AI Integration:** Powered by Google Gemini with graceful degradation to Mock mode when `GOOGLE_AI_API_KEY` is not provided.
- **Security & Privacy:** One-way SHA-256 Aadhaar hashing (no plaintext storage), AES-256-GCM bank account encryption, JWT with HTTP-only refresh tokens, and RBAC with 6 defined roles.

---

## Architecture & Technology Stack

| Layer | Technology | Description |
|---|---|---|
| **Frontend** | Next.js 14 + React 18 + TypeScript | Responsive portal with Tailwind CSS + shadcn/ui components |
| **Backend API** | FastAPI (Python 3.11+) | Async API, Pydantic v2 schemas, REST endpoints |
| **Database** | PostgreSQL 15 | Relational storage with 25+ models; SQLite supported for test |
| **Task Queue** | Celery + Redis | Asynchronous OCR and document intelligence pipeline |
| **Storage** | Local Filesystem / S3-compatible | Local filesystem storage (`storage/documents/`) by default |
| **AI / OCR** | Google Gemini / Vision (Optional) | Multi-modal document classification, quality check, and RAG |

---

## Quick Start (Docker)

```bash
# 1. Clone repository and enter directory
cd "e:/MoTA Scholarship"

# 2. Copy environment template and configure secrets
cp .env.example .env

# 3. Start services with Docker Compose
docker compose up --build

# 4. In a separate terminal, apply migrations and seed verified schemes:
docker compose exec api alembic upgrade head
docker compose exec api python infra/scripts/seed_schemes.py

# 5. Access services:
#    Frontend Portal:  http://localhost:3000
#    Interactive API:  http://localhost:8000/docs
#    Health Check:     http://localhost:8000/health
```

---

## Quick Start (Local Development without Docker)

### Backend (FastAPI)
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows

# Install dependencies
pip install -r apps/api/requirements.txt

# Run database migrations and seed official schemes
alembic -c apps/api/alembic.ini upgrade head
python infra/scripts/seed_schemes.py

# Start backend server
uvicorn main:app --app-dir apps/api --reload --port 8000
```

### Frontend (Next.js)
```bash
cd apps/web
npm install
npm run dev
```

---

## RBAC Roles

1. **`applicant`**: Student applicant registration, profile creation, application submission, deficiency resubmission.
2. **`verification_officer`**: L1 document verification and authenticity checking.
3. **`scrutiny_officer`**: L2 eligibility verification and compliance audit.
4. **`selection_committee`**: Merit ranking and selection review.
5. **`scheme_admin`**: Scheme rule, document, and form configuration.
6. **`super_admin`**: Platform administrator with system-wide audit access.

---

## Official Source Attribution
All scholarship and fellowship scheme rules and criteria are sourced directly from:
- **Ministry of Tribal Affairs Official Portal:** [https://tribal.nic.in/ScholarshiP.aspx](https://tribal.nic.in/ScholarshiP.aspx)
- **Direct Benefit Transfer (DBT) Tribal Portal:** [https://dbttribal.gov.in/](https://dbttribal.gov.in/)
- **National Scholarship Portal (NSP):** [https://scholarships.gov.in/](https://scholarships.gov.in/)

---

## Phase Architecture (Phases 1–8)

1. **Phase 1 — System Architecture & Foundation**: Local-first architecture design, Docker Compose stack, database models, and repository structure.
2. **Phase 2 — Core Platform & Identity**: RBAC (6 roles), bcrypt hashing, JWT access + refresh rotation, SHA-256 Aadhaar hashing, and AES-256-GCM field encryption.
3. **Phase 3 — Scheme & Versioned Eligibility Engine**: Deterministic rule evaluation, immutable published scheme versions, and dynamic form generation.
4. **Phase 4 — Applicant Portal & Workflow**: Multi-step application submission, document uploads, application version-locking, deficiency-response loop, and strict IDOR protection.
5. **Phase 5 — AI Document Intelligence Pipeline**: Assistive OCR and classification (Gemini/Vision), document quality assessment, malware quarantine, and officer-in-the-loop review.
6. **Phase 6 — Administrative Intelligence & Dashboards**: Truthful, database-derived analytics, workload tracking, scheme performance, and privacy-preserving CSV export.
7. **Phase 7 — Government Integration Readiness Framework**: Standardized adapter interfaces for UIDAI, DigiLocker, NSP, DBT, and MoTA Dashboard; all configured as truthful stubs with strict anti-fabrication controls.
8. **Phase 8 — Production Hardening & SIH Readiness**: Comprehensive security hardening (magic bytes, path traversal rejection, rate limiting, request correlation IDs, security headers, RBAC route locks), backup/recovery guides, and 82 automated regression tests.

---

## 🚨 Critical Government Integration Disclosure

> **Government integrations in this system (UIDAI/Aadhaar, DigiLocker, NSP, DBT, MoTA Dashboard) are integration-ready adapters.**
> They operate in **`stub`** mode by default and require authorized government credentials, API specifications, and access approvals before live connectivity can be enabled.
> The system **never fabricates** government responses, transactions, or verifications.

---

## SIH Demonstration Workflow

The system is demonstrable end-to-end locally without external paid cloud services or live government API credentials:
1. **Applicant Registration & Login**: Instant account creation with password hashing and JWT issuance.
2. **Scheme Discovery**: Browse 5 official MoTA scholarship schemes with verified eligibility criteria.
3. **Dynamic Application Form**: Rendered dynamically from the locked scheme version.
4. **Deterministic Eligibility Evaluation**: Rule engine checks age, income, category, and marks with complete rule traceability.
5. **Document Upload & Security**: Multi-format uploads (PDF/JPEG/PNG) protected by magic byte signature checks, filename normalization, and size limits.
6. **Assistive Document Processing**: OCR and quality analysis with transparent confidence scores (`AI SUGGESTION — NOT VERIFIED`).
7. **Human Officer Review**: Authorized scrutiny officer reviews documents, raises deficiencies, or verifies records.
8. **Government Integration Status**: Administrative panel displays truthful adapter configuration states (`REQUIRES_AUTHORIZED_ACCESS` / `NOT_CONFIGURED`).
9. **Administrative Analytics**: Real-time KPI cards, scheme distributions, and processing durations derived strictly from local records.
10. **Immutable Audit Trail**: Chronological, tamper-evident audit logs of all security and workflow events.

---

## Verification & Testing

Run full backend test suite (all 82 tests):
```bash
pytest apps/api/tests -v
```

Run frontend typecheck and production build:
```bash
cd apps/web
npx tsc --noEmit
npm run build
```

Backup & Disaster Recovery:
See [`docs/BACKUP_RECOVERY.md`](file:///E:/MoTA%20Scholarship/docs/BACKUP_RECOVERY.md) for local PostgreSQL and document storage backup and restoration procedures.


---

## Phase 11 Deliverables & Technical Evidence Package

The system has completed **Phase 10 (Final Implementation)** and **Phase 11 (SIH Final Submission, QA & Evidence Package)**.

### Comprehensive Evaluation Documentation:
- **[SIH_EVIDENCE_INDEX.md](SIH_EVIDENCE_INDEX.md)**: Full requirements traceability matrix connecting requirements to code, tests, and evidence.
- **[DEMO_GUIDE.md](DEMO_GUIDE.md)**: 39-step end-to-end evaluation demonstration runbook, test credentials, and safe reset instructions.
- **[SECURITY.md](SECURITY.md)**: Security architecture, RBAC boundaries, IDOR defense, file validation, and secret audit results.
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)**: Technical specifications and authorization prerequisites for UIDAI, DigiLocker, NSP, DBT, and MoTA adapters.
- **[TESTING.md](TESTING.md)**: QA test execution results (101/101 backend tests passed, frontend TypeScript clean, Next.js build clean).
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture diagram, component boundaries, and data flows.

### Safe Demonstration Reset:
To purge demo applications and restore a pristine state without touching official schemes:
```bash
python infra/scripts/demo_reset.py
```
