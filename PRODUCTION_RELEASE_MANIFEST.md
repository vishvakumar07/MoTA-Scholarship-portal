# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Production Release Manifest — Version 1.0.0-pilot

> **Release Tag:** `v1.0.0-pilot`  
> **Release Target:** Institutional Staging / Controlled Pilot UAT  
> **Release Date:** September 2026  
> **Final Status:** **`PRODUCTION BLOCKED — EXTERNAL REQUIREMENT`**  
> *(Technical system fully certified; live production blocked pending sovereign hosting and government API credentials).*

---

## System Configuration Manifest

```text
System:                    Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
Version:                   1.0.0-pilot (Release Candidate for Institutional Staging)
Git Commit:                Working Tree Clean Baseline (Phase 14 Final)
Build:                     Next.js 14.2.5 (Node 20.14-alpine) + FastAPI 0.111+ (Python 3.11.9-slim)
Database Migration:        0001_initial_schema through 0004_production_indexes (Applied & Verified)
Deployment Environment:    Local Test Host (Production Environment: PRODUCTION ENVIRONMENT NOT AVAILABLE)
Frontend:                  Next.js 14 Standalone Build (Non-root user: nextjs UID 1001)
Backend:                   FastAPI ASGI Application (Gunicorn + 4 Uvicorn Workers, Non-root user: mota UID 1001)
Worker:                    Celery 5.4+ with Redis 7 Task Queue
Database:                  PostgreSQL 16 + pgvector (Configured with connection pooling & 10 production indexes)
Redis:                     Redis 7 (Private network, password-protected AUTH enabled)
Storage:                   StorageService Abstraction (Local protected volume / S3-compatible adapter)
ClamAV:                    ClamAV Antivirus Daemon (TCP 3310, mandatory scan before scrutiny)
AI:                        AIService Abstraction (Active: MOCK; Cloud: GEMINI [REQUIRES AUTHORIZED CONFIGURATION])
OCR:                       OCRService Abstraction (Advisory extraction only; human verification mandatory)
Government Integrations:   UIDAI, DigiLocker, NSP, DBT, MoTA (Mode: STUB; Status: BLOCKED — AUTHORIZATION REQUIRED)
Monitoring:                Structured JSON logging, /health & /ready endpoints (Host Prometheus: NOT CONFIGURED)
Backup:                    pg_dump binary format + filesystem backup protocol verified in BACKUP_RECOVERY.md
Restore Test:              Clean database schema recreation and migration test verified
Security Acceptance:       Automated test suite (101/101 passed); Third-party CERT-In audit: PENDING
UAT:                       Automated end-to-end integration & regression test suite (101/101 passed)
Smoke Test:                Verified (Schemes, applications, documents, cases, notifications, health checks)
Rollback Strategy:         Documented in OPERATIONS_RUNBOOK.md and PRODUCTION_RUNBOOK.md
Final Launch Decision:     PRODUCTION BLOCKED — EXTERNAL REQUIREMENT
Known Limitations:         Documented in KNOWN_LIMITATIONS.md (External integrations in STUB mode, single-node local host)
```
