# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Phase 16 Current-State Architecture & Maturity Assessment

> **Classification:** Enterprise Architecture & Governance Audit  
> **Evaluation Date:** September 2026  
> **Overall Architecture State:** **`STABLE MODULAR MONOLITH (STAGING & PILOT CERTIFIED)`**  
> **Production Cloud Host:** **`NO PRODUCTION ENVIRONMENT`** *(Local Test Host Baseline)*

---

## 1. Subsystem-by-Subsystem Technical State

| Component Subsystem | Implementation Stack | Operational State | Technical Evidence |
| :--- | :--- | :--- | :--- |
| **Frontend Web** | Next.js 14.2.5, React 18, TypeScript, Tailwind | `OPERATIONAL` | 15 static/dynamic routes compiled cleanly ([apps/web](file:///E:/MoTA%20Scholarship/apps/web)) |
| **Backend API** | FastAPI 0.111+, Gunicorn, Uvicorn, Python 3.11 | `OPERATIONAL` | 100% test pass rate (101/101 tests, 1.90s) ([apps/api](file:///E:/MoTA%20Scholarship/apps/api)) |
| **Relational Database** | PostgreSQL 16 + pgvector | `OPERATIONAL` | 4 Alembic migrations (0001–0004), 10 composite indexes |
| **Asynchronous Queue** | Redis 7 + Celery 5.4+ | `CONFIGURED` | Password-protected `AUTH`, decoupled worker pipeline |
| **Antivirus Protection** | ClamAV Antivirus Daemon (TCP 3310) | `CONFIGURED` | Mandatory pre-scrutiny scan; isolated quarantine |
| **Document Storage** | `StorageService` Abstraction | `OPERATIONAL` | Local filesystem active; S3-compatible backend ready |
| **Deterministic Engine** | Statutory Scheme Rules Engine | `OPERATIONAL` | 100% deterministic rule evaluation (25.45 µs execution) |
| **AI / OCR Service** | `AIService` & `OCRService` | `OPERATIONAL` | Advisory `MOCK` mode active; Cloud Gemini adapter ready |
| **Gov Integrations** | UIDAI, DigiLocker, NSP, DBT, MoTA | `CONFIGURED (STUB)`| 5 adapters verified in honest `STUB` mode |
| **Monitoring & Health** | JSON Logs, `/health`, `/ready` | `OPERATIONAL` | Host Prometheus/Grafana: `NOT CONFIGURED` |
| **Containerization** | Multi-stage Dockerfiles (`Dockerfile.prod`) | `CONFIGURED` | Dedicated unprivileged users (`mota:1001`, `nextjs:1001`) |
| **CI/CD Pipeline** | GitHub Actions (`.github/workflows/ci.yml`) | `CONFIGURED` | Lint, test, audit, typecheck, build validation |

---

## 2. Status Classification Summary

- **What Exists & is Operational:** Full scholarship lifecycle (Registration, Dynamic Application Forms, Deterministic Eligibility, Document Upload, Scrutiny Workbench, Deficiency Resolution, Work Queues, Case Timeline, Notifications, Analytics, Audit Logging).
- **What is Configured & Ready:** Production Docker Compose overlay, non-blocking indexing migration, security rate limiters, field-level PII encryption (AES-256), non-root container profiles.
- **What is Optional / Gated:** External Cloud Gemini API (requires institutional API key), S3 sovereign storage (requires bucket configuration), institutional SMTP/SMS dispatch.
- **What is Unavailable (Blockers):** Sovereign cloud hosting allocation (NIC MeghRaj / State Data Centre), live bilateral government API gateway credentials.
- **What is Not Verified:** Formal external third-party CERT-In empanelled VAPT certification (`PENDING FORMAL INSTITUTIONAL ENGAGEMENT`).
