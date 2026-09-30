# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Security Operations (SecOps) & Continuous Vulnerability Management

> **Classification:** Security Operations Specification  
> **Status:** APPROVED OPERATIONAL SPECIFICATION (Phase 15)  
> **Target:** Continuous Hygiene, Supply-Chain Security, Attack Detection

---

## 1. Recurring Security Cadence

| Cadence | Operational Activity | Tooling / Command | Responsible Role |
| :--- | :--- | :--- | :--- |
| **Daily** | Audit log anomaly inspection (failed logins, account lockouts, 403 spikes). | SQL query on `audit_logs` | SecOps Analyst |
| **Weekly** | Dependency vulnerability scan (Python & Node.js). | `pip-audit`, `npm audit` | DevOps Engineer |
| **Weekly** | ClamAV antivirus database freshness verification. | `freshclam --check` | Platform Engineer |
| **Monthly** | Credential rotation review; IAM permission least-privilege verification. | Internal checklist | Lead SRE |
| **Quarterly** | External vulnerability assessment & penetration testing (VAPT). | CERT-In empanelled auditor | Institutional CISO |

---

## 2. Dependency & Vulnerability Management Protocol

1. **Scanning Execution:**
   - Python: Run `pip-audit` within `.venv` to detect CVEs against PyPI advisory database.
   - Frontend: Run `npm audit --production` in `apps/web` to detect Node.js package advisories.
2. **Remediation SLAs:**
   - **Critical (CVSS ≥ 9.0):** Remediation deployed within 48 hours.
   - **High (CVSS 7.0 – 8.9):** Remediation deployed within 7 calendar days.
   - **Medium (CVSS 4.0 – 6.9):** Addressed in next scheduled maintenance cycle.
   - **Low (CVSS < 4.0):** Evaluated and addressed as appropriate.
3. **Lock File Integrity:** All upgrades must be pinned in `requirements.txt` and `package-lock.json`. Unpinned floating dependencies are strictly prohibited in production.

---

## 3. Threat Monitoring & Anomaly Detection

SecOps monitors for measurable operational anomalies:
- **Brute Force Detection:** More than 5 failed login attempts for a single account triggers automated lockout (`user.locked_until = NOW() + 15 MINS`) and logs `AUTH_LOCKOUT`.
- **IDOR Probing Detection:** Multiple 403/404 responses on `/api/v1/applications/{id}` from a single IP or user account.
- **Malicious Upload Attempts:** Upload streams triggering ClamAV virus signatures (`INFECTED`) automatically isolate the file and flag the account.
- **Aadhaar Privacy Defense:** Automated log scraper verifies that no 12-digit integer matching Aadhaar Verhoeff regex ever appears in plaintext logs.
