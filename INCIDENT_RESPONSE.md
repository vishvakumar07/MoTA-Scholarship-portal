# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Production Security Incident Response Plan (IRP)

> **Classification:** Official Operational Security Procedure  
> **Status:** APPROVED BASELINE (Phase 14)  
> **Mandate:** Rapid Detection, Containment, Eradication, Recovery & Post-Incident Review  
> **Statutory Notice:** Legal notification timelines (e.g., CERT-In 6-hour cybersecurity reporting directive): `REQUIRES INSTITUTIONAL/LEGAL CONFIRMATION`.

---

## 1. Incident Response Lifecycle & Severity Classification

The platform adheres to the National Cyber Incident Response Framework across four operational severity tiers:

| Severity Level | Definition | Impact Scope | Initial Response Target | Escalation Authority |
| :--- | :--- | :--- | :--- | :--- |
| **SEV-1 (Critical)** | Active data breach of PII, unauthorized admin access, database destruction, ransomware, or key compromise. | Entire system / Public trust compromised | Immediate (< 15 mins) | Chief Information Security Officer (CISO) & MoTA Executive Leadership |
| **SEV-2 (High)** | Service outage of API or database, ClamAV bypass, failure of background workers affecting submissions. | Critical workflow blocked | < 1 hour | Technical Lead & Infrastructure Operations Lead |
| **SEV-3 (Medium)** | External integration adapter failure, localized IDOR attempt blocked, elevated 5xx error rate (< 5%). | Degraded performance / Non-critical | < 4 hours | Application Support Lead |
| **SEV-4 (Low)** | Minor bug, isolated non-malicious user login lockouts, informational security alert. | Negligible operational impact | Next business day | Platform Engineer |

---

## 2. Standard Operating Procedures (SOPs) for Key Scenarios

### 2.1 Scenario A: Personal Data (PII) Breach or Unauthorized Disclosure
1. **Detection:** Anomaly alerts on high-volume database exports, unauthorized queries to `/api/v1/applications`, or external disclosure report.
2. **Containment:**
   - Immediately revoke active JWT sessions by rotating `JWT_SECRET_KEY` and flushing Redis cache (`FLUSHDB` on session DB).
   - Restrict API access to internal maintenance IP addresses at reverse proxy/WAF.
3. **Investigation:**
   - Query `audit_logs` table for actor IDs, target entity IDs, timestamps, and request IPs:
     ```sql
     SELECT * FROM audit_logs WHERE action IN ('APPLICATION_EXPORT', 'UNAUTHORIZED_ACCESS_ATTEMPT') AND created_at >= NOW() - INTERVAL '24 HOURS';
     ```
   - Verify whether `FIELD_ENCRYPTION_KEY` remained uncompromised.
4. **Recovery:**
   - Terminate compromised user accounts and regenerate credentials.
   - Restore database to pre-compromise verified snapshot if data was tampered with.
5. **Notification:** File formal cybersecurity incident report with CERT-In and nodal ministry authority (`REQUIRES INSTITUTIONAL/LEGAL CONFIRMATION`).

### 2.2 Scenario B: Malware Detection or Upload Bypass Attempt
1. **Detection:** ClamAV daemon alerts on infected file stream (`status: INFECTED`), or post-upload heuristic alert.
2. **Containment:**
   - The document upload pipeline immediately marks the document `malware_scan_status = 'INFECTED'` and quarantines the file.
   - The file is deleted from `apps/api/storage/uploads/` and quarantined in an isolated, non-executable directory.
3. **Investigation:**
   - Identify applicant user ID, client IP, original filename, and SHA-256 file hash.
   - Inspect whether any background OCR or worker process attempted parsing prior to quarantine.
4. **Recovery:**
   - Issue automated security notification to applicant indicating document rejection due to policy violation.
   - Flag applicant account for scrutiny review if multiple malicious payloads are detected.

### 2.3 Scenario C: Cryptographic Credential or Secret Leakage
1. **Detection:** Secret detected in public repository, build log, or unauthorized server environment dump.
2. **Containment:**
   - Execute emergency secret rotation for compromised keys:
     - `JWT_SECRET_KEY`: Immediate replacement invalidates all current tokens.
     - `DATABASE_URL`: Rotate password in PostgreSQL and update container secret.
     - `REDIS_PASSWORD`: Update `requirepass` in Redis and restart worker containers.
     - `FIELD_ENCRYPTION_KEY`: If breached, initiate data re-encryption migration protocol immediately.
3. **Recovery:** Deploy updated configuration container images via CI/CD pipeline.

### 2.4 Scenario D: Database Corruption or Host Storage Failure
1. **Detection:** PostgreSQL container crashing with I/O errors, corruption in transaction logs, or storage volume exhaustion.
2. **Containment:**
   - Gracefully stop FastAPI application server to prevent partial or inconsistent transactions:
     ```bash
     docker compose stop api worker
     ```
3. **Recovery:**
   - Verify filesystem integrity (`fsck`).
   - Restore latest verified binary dump (`pg_restore -Fc`) into clean PostgreSQL instance per [BACKUP_RECOVERY.md](file:///E:/MoTA%20Scholarship/BACKUP_RECOVERY.md).
   - Replay WAL files up to point of failure.
   - Verify data integrity and resume services.

### 2.5 Scenario E: Government Integration Gateway Compromise or Anomaly
1. **Detection:** Unexpected response payloads from external government endpoints, authentication failures, or SSL certificate mismatch.
2. **Containment:**
   - Immediately switch adapter mode from `LIVE` to `STUB` via environment toggle (`UIDAI_INTEGRATION_MODE=STUB`).
   - The application automatically degrades gracefully, displaying honest advisory notice `REQUIRES AUTHORIZED ACCESS`.
3. **Investigation:** Coordinate with NIC/UIDAI/DigiLocker nodal officers to verify gateway status.

---

## 3. Communication, Documentation & Post-Mortem

- **Incident Commander:** Appointed lead coordinating technical and communications streams.
- **War Room:** Secure audio/video channel and dedicated incident response log.
- **Root Cause Analysis (RCA):** Mandatory post-mortem document delivered within 72 hours of incident closure detailing timeline, root cause, impact, and preventive remediation actions.
