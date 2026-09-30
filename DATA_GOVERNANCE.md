# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Data Governance, Classification & Lifecycle Policy

> **Classification:** Official Institutional Data Governance Framework  
> **Status:** RATIFIED PILOT SPECIFICATION  
> **Compliance Target:** Digital Personal Data Protection Act (DPDPA), 2023 / IT Act, 2000  
> **Notice:** Statutory retention periods and official archival schedules require institutional confirmation (`OFFICIAL INFORMATION REQUIRED`).

---

## 1. Data Classification Matrix

The platform classifies all managed data into seven distinct categories to enforce confidentiality, integrity, availability, and lifecycle governance:

| Data Category | Description | Sensitivity Level | Encryption at Rest | Encryption in Transit | Access Boundary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Public / Reference Data** | Scheme guidelines, eligibility rules, version catalogues, public notifications. | Public | Standard disk encryption | TLS 1.3 / HTTPS | Unrestricted read access. |
| **2. Applicant Profile & Data** | Names, contact details, caste category, annual income, institution, bank account details. | Confidential / PII | Field-level Fernet (AES-256) + DB disk encryption | TLS 1.3 / HTTPS | Applicant (self) & Authorized Scrutiny Officers. |
| **3. Identity Credentials (Aadhaar)** | 12-digit Aadhaar number, biometric tokens, e-KYC reference. | Restricted / Highly Sensitive | **One-way SHA-256 hash only**; raw 12-digit UID is **NEVER STORED**. | TLS 1.3 / HTTPS | Zero storage of raw UID. Hash used only for de-duplication. |
| **4. Uploaded Documents** | Caste certificates, income certificates, marksheets, disability certificates (PDF/PNG/JPEG). | Confidential / PII | Storage bucket / filesystem encryption | TLS 1.3 / HTTPS | Scrutiny Officer & Document Owner. No public URL access. |
| **5. AI-Derived & OCR Data** | Extracted text, confidence scores, detected names/dates, discrepancy flags. | Internal / Advisory | Database disk encryption | TLS 1.3 / HTTPS | Officers & System Services. Advisory only. |
| **6. Operational & Case Data** | Case assignments, deficiency notices, scrutiny remarks, workflow timestamps. | Internal Official | Database disk encryption | TLS 1.3 / HTTPS | Scrutiny Officers, Scheme Admins, Super Admins. |
| **7. Audit & Security Logs** | User login, state transitions, document access, IP hashes, actor IDs, integration traces. | Tamper-Evident / High | Immutable append-only log storage | TLS 1.3 / HTTPS | Super Admin & Security Auditors. Non-modifiable. |

---

## 2. Category-Specific Governance & Lifecycle Policies

### 2.1 Public & Reference Data
- **Purpose:** Informing applicants and institutions about scheme requirements, eligibility rules, and quotas.
- **Storage:** PostgreSQL `schemes`, `scheme_versions`, `scheme_rules`.
- **Retention:** Permanent. Historical scheme versions are archived with immutable timestamps (`is_active = false`) and are never deleted, ensuring historical application reproducibility.
- **Deletion:** Deletion prohibited; archival only.

### 2.2 Applicant Personal Data (PII)
- **Purpose:** Establishing identity, tribal community membership, financial eligibility, and academic qualification.
- **Storage:** PostgreSQL `users`, `applicant_profiles`, `applications`. Sensitive fields encrypted with `FIELD_ENCRYPTION_KEY`.
- **Retention:** Retained for the duration of the scholarship award plus the statutory post-disbursement audit period (`OFFICIAL INFORMATION REQUIRED` for exact statutory duration).
- **Deletion:** Upon authorized administrative request or formal right-to-erasure determination under DPDPA, applicant records are anonymized in compliance with statutory audit preservation rules.

### 2.3 Document Storage Governance
- **Purpose:** Substantiating claims made in scholarship applications.
- **Storage:** Abstracted via `StorageService`. Default: local protected filesystem (`apps/api/storage/uploads/`). Production option: S3-compatible sovereign object storage.
- **Access Control:** File downloads require authenticated session authorization via `GET /api/v1/documents/{id}/download`. Direct filesystem or static URL exposure is strictly prohibited.
- **Integrity & Security:** Every uploaded file undergoes MIME validation, extension verification, filename UUID sanitization, and ClamAV antivirus scanning prior to officer scrutiny.

### 2.4 AI-Derived Data
- **Purpose:** Assisting scrutiny officers by detecting low-quality scans, extracting certificate issuance dates, and flagging inconsistencies.
- **Storage:** PostgreSQL `document_extractions`, `application_ai_analyses`.
- **Retention:** Tied to the parent application lifecycle.
- **Human Oversight Guarantee:** AI data is explicitly labeled as `advisory`. Under no circumstances does an AI model or OCR extraction automatically approve or reject an applicant.

### 2.5 Operational & Workflow Data
- **Purpose:** Tracking case progress, officer workloads, and deficiency resolution.
- **Storage:** PostgreSQL `cases`, `deficiency_notices`, `notifications`.
- **Retention:** Retained through the active academic sanction cycle and subsequent institutional audit.

### 2.6 Audit Log Governance
- **Purpose:** Accountability, forensic review, and compliance verification.
- **Storage:** PostgreSQL `audit_logs`.
- **Integrity Controls:** Append-only table. Updates (`UPDATE`) and deletions (`DELETE`) are prohibited at the database role level in production.
- **Retention:** Minimum 7 years or as prescribed by national archives policy (`OFFICIAL INFORMATION REQUIRED`).

### 2.7 Government Integration Data
- **Purpose:** Verifying identity, student status, and DBT disbursement records against authorized national systems.
- **Storage:** PostgreSQL `government_verifications`.
- **Data Minimization:** Only transaction tokens, verification timestamps, and verification status (`VERIFIED`, `FAILED`, `PENDING`) are retained. Raw Aadhaar payloads or unnecessary biometric metadata are never stored.

---

## 3. Data Protection Safeguards Summary

1. **Aadhaar Protection:** Full compliance with UIDAI regulations — raw Aadhaar numbers are never persisted to disk or logs; only cryptographic SHA-256 hashes are used for de-duplication.
2. **Field-Level Encryption:** Applicant bank account numbers, IFSC codes, and mobile numbers are encrypted using AES-256 (Fernet) prior to database insertion.
3. **No Direct Document URL Exposure:** All documents are stored under randomized UUIDs without original filenames in storage paths, and downloads are gated through FastAPI session authorization.
4. **Least-Privilege Isolation:** Application database user accounts do not possess administrative DDL permissions during normal operations.
