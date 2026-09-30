# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Business Continuity & Safe Degraded Operations Plan

> **Classification:** SRE & Business Continuity Specification  
> **Status:** APPROVED OPERATIONAL SPECIFICATION (Phase 16)  
> **Mandate:** Graceful Degradation Without Workflow Blockage

---

## 1. Safe Degraded Mode Matrix

| Failed Subsystem | Impact on Application | Fallback Mechanism & Operational State |
| :--- | :--- | :--- |
| **External AI API** | Advisory OCR text extraction unavailable. | **FAIL-OPEN:** System displays `AI Unavailable - Manual Review Mandatory`. Eligibility evaluation and officer scrutiny continue normally. |
| **ClamAV Antivirus Daemon**| Real-time malware scanning paused. | **FAIL-SAFE:** Uploaded documents marked `UNAVAILABLE` and queued for scan. Officer viewing is blocked until scanning resumes. |
| **Government Integration Adapters** | External identity or document verification offline. | **FAIL-SAFE:** System records status `REQUIRES_AUTHORIZED_ACCESS` / `PENDING`. Officers verify certificates manually. **Never fabricate approvals.** |
| **External SMTP / SMS** | Outbound notification delivery paused. | **FAIL-OPEN:** Notifications persist in PostgreSQL `notifications` table; visible immediately in citizen in-app portal. |
| **Redis / Task Queue** | Asynchronous job execution delayed. | Tasks buffer in persistent Redis queue; processed sequentially upon worker restart. |
| **Primary Database (HA Failover)**| Read/write transactions temporarily paused. | Connection pool automatically reconnects to promoted replica within 30 seconds. |
