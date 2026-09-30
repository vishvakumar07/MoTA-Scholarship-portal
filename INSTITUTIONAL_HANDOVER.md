# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Institutional Handover & Custody Transfer Specification

> **Classification:** Official Institutional Architecture & Handover Documentation  
> **Status:** READY WITH CONDITIONS  
> **Target Scope:** Transition from Validated Pilot / SIH Prototype to Authorized Sovereign Operation  
> **Compliance Notice:** This document strictly reflects verified system capabilities. No governmental credentials, API keys, or operational authorizations are fabricated. All pending institutional entities, nodal roles, and statutory policies are marked `OFFICIAL INFORMATION REQUIRED`.

---

## 1. System Ownership & Operational Custody Matrix

The platform is designed to be operated under sovereign institutional oversight. The custody boundaries across all components are defined below:

| Subsystem Component | Operational Custody Role | Infrastructure Responsibility | Custody Boundary & Authorization Required |
| :--- | :--- | :--- | :--- |
| **Web Frontend** (`apps/web`) | Institutional Web Operations Team | Static / Next.js Node.js Hosting | Domain ownership, SSL/TLS certificate installation, CDN/WAF configuration. |
| **API Gateway & Core API** (`apps/api`) | Institutional Application Operations Team | FastAPI ASGI Services | Application monitoring, process supervisors, ASGI worker scaling, port binding. |
| **Relational Database** | Database Administrator (DBA) Team | PostgreSQL 16 + pgvector Cluster | Connection pooling, replication, physical backup schedules, WAL archiving, DB user least-privilege. |
| **Asynchronous Task Workers** | Platform Operations Team | Celery + Redis Task Queue | Worker process monitoring, queue depth alerts, concurrency tuning, dead-letter recovery. |
| **Document & Object Storage** | Storage Administration Team | S3-Compatible / Local Storage | Storage bucket access policies, disk encryption at rest, retention lifecycle, immutable audit storage. |
| **Malware Scanning** | Information Security Team | ClamAV / ICAP Server | Regular virus database definitions updates (`freshclam`), quarantine inspection. |
| **AI / Document Intelligence** | AI Governance & Verification Officer | Gemini / Local / Mock Engine | API quota allocation, rate limiting, human oversight escalation, non-decision-making audit. |
| **Government Integration Adapters** | Official Government Liaison / API Team | External Secure Gateway Adapters | MoU execution, IP whitelisting, OAuth/mTLS credentials, production endpoint configuration. |

*Note: Specific organizational units, designated nodal officers, and contact directories are: `OFFICIAL INFORMATION REQUIRED`.*

---

## 2. Operational Responsibilities

Institutional operation requires clear separation of duties:

### 2.1 Scheme Administration (MoTA / Authorized Directorate)
- Official publication of scholarship/fellowship guidelines and versioned eligibility criteria.
- Authorization and review of academic year cutoffs, reservation criteria, and allowance quotas.
- Scheme retirement or archival under strict data preservation rules.

### 2.2 Scrutiny & Verification Officers
- Verification of applicant-submitted income, caste, disability, and academic certificates.
- Issuing structured deficiency notices requesting clarification or re-upload.
- Recommendation or rejection with recorded justifications and tamper-evident audit logging.
- Verification that automated AI checks remain strictly advisory.

### 2.3 System Administrators & DevOps
- Applying schema migrations via Alembic with verified backup checkpoints.
- Managing secure environment secret injection (Docker secrets / HashiCorp Vault / KMS).
- Monitoring system health, error rates, queue depths, and disk utilization.
- Executing routine backup validation and disaster recovery drills.

### 2.4 Information Security & Compliance Officers
- Periodic vulnerability assessments, penetration testing, and dependency audit.
- Review of tamper-evident audit logs (`AuditLog` records).
- Access control reviews ensuring least privilege and immediate revocation upon personnel transfer.

---

## 3. Required Credential Categories

The system strictly decouples code from configuration. The institutional deployment team must supply the following credential categories prior to live launch. **No actual credentials are stored in source control.**

| Credential Category | Variable / Target | Format / Specification | Custody & Rotation Policy |
| :--- | :--- | :--- | :--- |
| **Database Master Credentials** | `DATABASE_URL` | PostgreSQL connection URI with strong alphanumeric password | Owned by DBA team; rotated per institutional policy. |
| **Cache & Queue Credentials** | `REDIS_URL` | Redis URI with strong `AUTH` password | Internal private network access only; rotated quarterly. |
| **JWT Signing Secret** | `JWT_SECRET_KEY` | Cryptographically random string (min 64 chars / 256 bits) | Rotated annually or immediately upon suspected compromise. |
| **Field-Level Encryption Key** | `FIELD_ENCRYPTION_KEY` | Fernet/AES-256 base64-encoded key | Never logged; requires data re-encryption migration if rotated. |
| **Antivirus Service Target** | `CLAMAV_HOST`, `CLAMAV_PORT` | TCP host & port of internal ClamAV daemon | Managed by platform security; internal IP only. |
| **Document Storage Target** | `STORAGE_BACKEND`, credentials | Storage path or S3-compatible IAM keys | Least-privilege IAM policy allowing PutObject/GetObject. |
| **AI Processing Gateway** | `GEMINI_API_KEY` | Official Cloud API Key or local engine path | `REQUIRES AUTHORIZED CONFIGURATION` (fallback: mock mode). |
| **Government API Gateways** | Adapters for UIDAI, DigiLocker, NSP, DBT, MoTA | mTLS client certs, API keys, OAuth client credentials | `REQUIRES AUTHORIZED CONFIGURATION` per official MoU. |

---

## 4. Required Approvals & Authorizations Checklist

Before moving this platform into official government production service, the following formal authorizations are required:

- [ ] **Infrastructure & Network Approval:**
  - Official hosting infrastructure allocated (NIC / State Data Centre / Authorized Sovereign Cloud).
  - Production domain name registered and official SSL/TLS wildcard/SAN certificate issued.
  - Reverse proxy / WAF configured with rate limiting and DDoS mitigation.
- [ ] **Security Certification:**
  - Third-party CERT-In empanelled security audit completed.
  - Static Application Security Testing (SAST) and Dynamic Application Security Testing (DAST) passed.
  - Vulnerability Assessment and Penetration Testing (VAPT) clearance certificate issued.
- [ ] **Data Sharing & Integration MoUs:**
  - **UIDAI / Aadhaar:** Authorized Authentication User Agency (AUA) / e-KYC User Agency (KUA) license and signed MoU.
  - **DigiLocker:** Official API onboarding and DigiLocker partner registration credentials.
  - **National Scholarship Portal (NSP):** Cross-portal de-duplication API authorization.
  - **Direct Benefit Transfer (DBT) / PFMS:** Official sanction order and DBT Bharat / PFMS payment gateway access.
  - **Ministry of Tribal Affairs (MoTA):** Official departmental sanction as the designated operating portal.
- [ ] **Privacy & Legal Clearances:**
  - Compliance verification under the Digital Personal Data Protection Act (DPDPA), 2023.
  - Public privacy notice, terms of service, and Aadhaar consent declaration approved by legal counsel.
- [ ] **Operational Handover Sign-off:**
  - Formal sign-off between development team and institutional operations directorate.

---

## 5. Decommissioning & Pilot Transition Procedure

1. **Demo Data Isolation:** Under no circumstances should test applicants or pilot databases be migrated to production.
2. **Schema Baseline:** Apply migrations sequentially (`0001` through `0004`) on a blank production PostgreSQL instance.
3. **Official Scheme Seeding:** Seed schemes strictly using the verified statutory guidelines (`01_national_fellowship_st.json`, `02_top_class_education_st.json`, `03_national_overseas_st.json`).
4. **Adapter Inactivity Verification:** Ensure all external integration flags remain in `STUB` or `MOCK` mode until live gateway authorization certificates are formally validated in a staging environment.

---

*Document finalized for institutional transmission. All pending official contacts and agency identifiers: `REQUIRES AUTHORIZED CONFIGURATION`.*
