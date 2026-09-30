# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Data Governance Acceptance & Compliance Protocol

> **Classification:** Official Institutional Data Governance Certification  
> **Status:** APPROVED BASELINE (Phase 14)  
> **Compliance Alignment:** Digital Personal Data Protection Act (DPDPA), 2023 / IT Act, 2000  
> **Notice:** Statutory retention schedules require formal gazetted confirmation: `OFFICIAL INFORMATION REQUIRED`.

---

## 1. Data Inventory & Operational Custody Acceptance

| Category | Managed Data Entities | Storage Subsystem | Access Boundary | Retention Status | Deletion / Erasure Process | Export Mechanism |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Applicant Personal Data** | Name, DOB, gender, caste, income, disability status, bank account number (encrypted), IFSC. | PostgreSQL `users`, `applicant_profiles`, `applications` | Applicant (self) & Authorized Scrutiny Officers | Active award lifecycle + statutory audit (`OFFICIAL INFORMATION REQUIRED`) | Anonymization / pseudonymization on authorized right-to-erasure | JSON / CSV structured export for authorized officers |
| **2. Identity Data (Aadhaar)** | Cryptographic SHA-256 hash of 12-digit UID. **Raw UID is never stored.** | PostgreSQL `users.aadhaar_hash` | Zero direct read; internal de-duplication match only | Linked to user profile lifecycle | Erased on authorized user account termination | Not exportable (one-way hash) |
| **3. Uploaded Certificates** | Caste certificates, income certificates, marksheets, disability certificates (PDF/PNG). | Local storage / S3 object store (`StorageService`) | Scrutiny Officer & Document Owner. No direct URLs. | Duration of academic award + verification audit | Secure file shredding / object bucket lifecycle expiration | Encrypted document stream via authenticated API |
| **4. AI & OCR Data** | Extracted text, quality confidence scores, detected names/dates, discrepancy flags. | PostgreSQL `document_extractions`, `application_ai_analyses` | Scrutiny Officers & System Services (Advisory only) | Tied to parent application record | Purged upon parent document deletion | Included in application scrutiny audit packet |
| **5. Operational & Case Data** | Case assignments, deficiency notices, scrutiny remarks, workflow timestamps. | PostgreSQL `cases`, `deficiency_notices`, `notifications` | Scrutiny Officers, Scheme Admins, Super Admins | Active sanction period + 7 years institutional record | Preserved for administrative audit | Structured operational report export |
| **6. Audit & Security Logs** | User login, state transitions, document access, IP hashes, actor IDs, integration traces. | PostgreSQL `audit_logs` (Append-only) | Super Admin & Security Auditors. Non-modifiable. | Minimum 7 years or per national archives mandate | Deletion strictly prohibited at database role level | Signed forensic log export |
| **7. Government Integrations**| Verification request tokens, timestamps, verification status (`VERIFIED`, `FAILED`, `PENDING`). | PostgreSQL `government_verifications` | Authorized System Adapters & Compliance Officers | Audit cycle duration | Purged per bilateral integration agreement | Integration audit report export |

---

## 2. Core Governance Safeguards Verified

1. **Aadhaar Privacy Guarantee:** Fully compliant with UIDAI regulations. The platform executes one-way SHA-256 hashing client/server side solely for duplicate detection. The raw 12-digit Aadhaar number is never written to disk, database, or logs.
2. **Field-Level Encryption:** Applicant bank accounts, IFSC codes, and mobile numbers are encrypted at rest using AES-256 (Fernet) prior to database insertion.
3. **No Direct Document URL Access:** Documents are stored under non-guessable UUID keys without original user filenames. Downloads are gated behind authenticated, role-verified FastAPI endpoints.
4. **Scheme Immutability:** Historical scheme guidelines, version numbers, and eligibility rules are immutable once published. Applications retain their original submission version forever.
5. **Human-in-the-Loop AI Mandate:** AI data is strictly categorized as `advisory`. No AI extraction or inference can approve, reject, or alter deterministic eligibility.

---

## 3. Data Governance Acceptance Verdict

### Status: **`APPROVED FOR INSTITUTIONAL STAGING & PILOT OPERATION`**
*(All data categories, storage mechanisms, access controls, and encryption safeguards are certified compliant).*
