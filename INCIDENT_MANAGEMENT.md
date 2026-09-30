# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Post-Launch Incident Management Framework & Operating Protocol

> **Classification:** SRE & DevOps Incident Management Policy  
> **Status:** APPROVED OPERATIONAL SPECIFICATION (Phase 15)  
> **Mandate:** Rapid Triage, Evidence Preservation, Blameless Post-Mortem, Root Cause Resolution

---

## 1. Severity Classification Matrix

| Severity Tier | Operational Impact | Target Response | Target Resolution | Escalation Authority |
| :--- | :--- | :--- | :--- | :--- |
| **P0 (Critical)** | Complete portal outage, active data breach, cryptographic key leak, or database corruption. | Immediate (< 15 mins) | < 4 hours | CISO, MoTA Executive Leadership, Lead SRE |
| **P1 (High)** | Core workflow blocked (e.g. application submission failing, document upload pipeline down, officer scrutiny queue inaccessible). | < 30 mins | < 8 hours | Lead SRE, Backend Operations Lead |
| **P2 (Medium)** | Non-blocking degradation (e.g. background OCR delayed, external integration stub reporting timeout, notification delivery retrying). | < 2 hours | Next business day | Application Support Team |
| **P3 (Low)** | Minor cosmetic defect, non-blocking UI anomaly, single-user transient error. | Next business day | Scheduled release | Software Engineering Team |

---

## 2. End-to-End Incident Lifecycle

```text
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ 1. DETECTION│ ───> │  2. TRIAGE  │ ───> │3.CONTAINMENT│ ───> │4.INVESTIGATE│
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
                                                                      │
┌─────────────┐      ┌─────────────┐      ┌─────────────┐             │
│8. POST-MORTM│ <─── │ 7. VERIFY   │ <─── │ 6. RECOVERY │ <───────────┘
└─────────────┘      └─────────────┘      └─────────────┘ (5. REMEDIATION)
```

1. **Detection:** Automated health check failure (`/ready` returning 503), error rate alert, or user report.
2. **Triage:** Incident Commander assigned; severity classified; war room opened.
3. **Containment:** Isolate affected subsystem (e.g. switch integration adapter to `STUB`, isolate infected document, or rate limit suspicious IP).
4. **Investigation:** Query structured application logs (`X-Request-ID`) and `audit_logs` without exposing PII.
5. **Remediation & Recovery:** Apply hotfix, failover to replica, or restore from verified backup.
6. **Verification:** Validate critical smoke test endpoints and application workflow.
7. **Post-Mortem:** Conduct blameless review and publish `POST_INCIDENT_<DATE>.md` within 72 hours.

---

## 3. Component-Specific Incident Playbooks

### 3.1 PostgreSQL Outage or Replication Failure
1. Inspect container/service status: `docker compose ps postgres`.
2. Check PostgreSQL error logs for storage exhaustion (`No space left on device`) or WAL corruption.
3. If database crashed due to storage, expand volume and restart.
4. If database corrupted, execute restore procedure from latest verified binary dump per [BACKUP_RECOVERY.md](file:///E:/MoTA%20Scholarship/BACKUP_RECOVERY.md).

### 3.2 Redis & Celery Task Worker Outage
1. Inspect Redis availability: `redis-cli ping`.
2. Check Celery worker process logs for unhandled memory leaks or killed worker processes.
3. Clear stuck task lock keys if worker crashed mid-task; restart worker pool:
   ```bash
   docker compose restart worker redis
   ```

### 3.3 ClamAV Antivirus Daemon Failure
1. If ClamAV becomes unreachable, the upload pipeline automatically fails-safe by marking scan status `UNAVAILABLE` and withholding document from scrutiny.
2. Restart ClamAV service: `docker compose restart clamav`.
3. Re-queue unscanned documents for scanning. **Never mark unscanned files as `CLEAN`.**

### 3.4 AI Service Outage or Quota Exhaustion
1. If cloud Gemini API errors (429 Rate Limit / 503 Unavailable), the system falls back to `MOCK` or `UNAVAILABLE`.
2. Operational scholarship eligibility continues unimpeded via deterministic rule engine.
3. Document scrutiny displays advisory alert: `AI Service Unavailable - Manual Review Mandatory`.

---

## 4. Post-Incident Review Template (`POST_INCIDENT_<DATE>.md`)

Every P0 or P1 incident requires a formal review document containing:
- **Incident Summary:** Date, duration, severity, affected services.
- **Timeline:** Key milestones from initial trigger to resolution.
- **Root Cause Analysis (RCA):** Five Whys analysis establishing technical and process root causes.
- **What Went Well / What Failed:** Objective blameless review.
- **Corrective Action Items:** Tracked engineering improvements with assigned owners and deadlines.
