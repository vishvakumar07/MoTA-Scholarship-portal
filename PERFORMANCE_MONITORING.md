# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Application Performance Monitoring (APM) & Capacity Guidelines

> **Classification:** SRE & Performance Engineering Guide  
> **Status:** APPROVED OPERATIONAL SPECIFICATION (Phase 15)  
> **Baseline Evidence:** Measured Local-First Benchmarks

---

## 1. Measured Performance Baselines (Local Host Benchmark)

| Subsystem / Operation | Measured Metric | Service Level Target (SLA) | Operational Status |
| :--- | :--- | :--- | :--- |
| **API Liveness Probe (`GET /health`)** | 90.2 ms | < 150 ms | **OPTIMAL** |
| **Scheme Discovery (`GET /api/v1/schemes`)** | 3.77 ms | < 50 ms | **OPTIMAL** |
| **Deterministic Rule Engine Evaluation** | 25.45 µs | < 5 ms | **HIGH PERFORMANCE** |
| **Storage Document Write (Local Disk)** | 0.18 ms | < 50 ms | **OPTIMAL** |
| **Password Verification (bcrypt 12 rounds)** | 89.39 ms | 70 – 120 ms | **CRYPTOGRAPHICALLY INTENDED** |
| **Aadhaar De-duplication Hash (SHA-256)** | 0.88 µs | < 10 µs | **HIGH PERFORMANCE** |
| **Backend Test Suite Execution (101 tests)**| 1.99 s | < 10 s | **OPTIMAL** |

---

## 2. Database Query Performance & Indexing

The platform enforces index-backed queries for high-cardinality searches via migration `0004_production_indexes.py`:
- `applications(applicant_id, status)`: Accelerates citizen dashboard loading.
- `applications(submitted_at DESC)`: Powers officer chronological work queues.
- `documents(application_id, status)`: Speeds up document scrutiny rendering.
- `audit_logs(user_id, created_at DESC)`: Optimizes user activity history retrieval.

**Slow Query Threshold:** Any database query exceeding **200 ms** in production must be flagged, logged with execution plan (`EXPLAIN ANALYZE`), and analyzed for index tuning.

---

## 3. Celery Queue & Background Job Monitoring

- **Monitored Queues:** `default`, `malware_scan`, `ocr_extraction`, `notifications`.
- **Queue Backlog Alert Threshold:** More than **50 pending tasks** in any queue triggers automated scaling or investigation alert.
- **Task Execution Time Limit:** Hard timeout of **120 seconds** per task prevents hung OCR or ClamAV processes from blocking worker threads.
