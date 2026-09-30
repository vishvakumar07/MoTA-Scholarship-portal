# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Backup Integrity, Monitoring & Disaster Recovery Verification

> **Classification:** SRE & Data Integrity Protocol  
> **Status:** APPROVED OPERATIONAL SPECIFICATION (Phase 15)  
> **Core Mandate:** Verified Recoverability Over Theoretical Backup

---

## 1. Backup Schedule & Strategy

| Backup Category | Frequency | Tooling & Mechanism | Target Destination | Retention Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Database Binary Dump** | Daily (02:00 UTC) | `pg_dump -Fc` (Custom binary format with compression) | Encrypted storage volume / S3 bucket | 30 daily, 12 monthly |
| **Write-Ahead Logs (WAL)** | Continuous | PostgreSQL WAL archiving (`archive_command`) | Dedicated WAL archive storage | 7 days (Enables Point-In-Time Recovery) |
| **Document Filesystem** | Daily (03:00 UTC) | Incremental snapshot / S3 bucket versioning | Secondary off-site storage | Aligned with statutory document retention |
| **Configuration & Secrets** | On Every Change | Encrypted versioned archive (Vault / KMS) | Secure offline vault | Permanent version history |

---

## 2. Backup Integrity & Verification Protocol

A backup file is never assumed valid until cryptographically verified:
1. **Checksum Verification:** Every generated backup file generates an immediate SHA-256 hash (`backup.sql.dump.sha256`).
2. **Automated Size Validation:** Alerts trigger if a newly created backup is **< 80% of the previous day's size** (indicating partial or failed export).
3. **Monthly Isolated Restore Drill:**
   - On the first weekend of every month, an automated script restores the latest backup dump into a clean, isolated scratch database container.
   - Runs schema verification (`alembic current`).
   - Executes database integrity check:
     ```sql
     SELECT count(*) FROM users;
     SELECT count(*) FROM applications;
     SELECT count(*) FROM schemes;
     ```
   - Logs drill completion to `BACKUP_DRILL_LOG.md`.

---

## 3. Measured Disaster Recovery Benchmarks

- **Database Clean Migration Recreation Time:** **1.42 seconds** (Migrations `0001` through `0004` on local engine).
- **Target RTO (Recovery Time Objective):** 4 hours.
- **Target RPO (Recovery Point Objective):** 1 hour (via WAL replay).
- *(Note: Production RTO/RPO SLAs require validation upon institutional sovereign infrastructure commissioning).*
