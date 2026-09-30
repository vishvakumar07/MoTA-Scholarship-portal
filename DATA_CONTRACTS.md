# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Canonical Data Contracts & Source-of-Truth Hierarchy

> **Classification:** Enterprise Data Architecture Specification  
> **Status:** RATIFIED BASELINE (Phase 17)  
> **Core Mandate:** Unambiguous Field Ownership; Zero Silent Overwriting; Strict Privacy Controls

---

## 1. Canonical Entity Contracts

### 1.1 Applicant Profile Entity
- **Source of Truth:** MoTA Scholarship Portal (Verified by Authenticated Citizen)
- **Sensitive Classification:** Confidential / PII
- **Fields:**
  - `id`: UUID (Primary Key, Required)
  - `user_id`: UUID (Foreign Key to `users.id`, Required)
  - `full_name`: String (Required, Input validation: alphabetic + spaces)
  - `date_of_birth`: Date (Required, ISO-8601 `YYYY-MM-DD`)
  - `gender`: Enum (`MALE`, `FEMALE`, `TRANSGENDER`, Required)
  - `caste_category`: String (Required, Strictly `"ST"` for MoTA schemes)
  - `sub_tribe`: String (Optional)
  - `annual_family_income`: Decimal (Required, Currency INR)
  - `state_of_domicile`: String (Required, Official Indian State/UT code)
  - `bank_account_encrypted`: String (Encrypted Fernet AES-256, Required)
  - `ifsc_code`: String (Required, Regex: `^[A-Z]{4}0[A-Z0-9]{6}$`)

### 1.2 Application Entity
- **Source of Truth:** MoTA Application Service
- **Sensitive Classification:** Official Internal Record
- **Fields:**
  - `id`: UUID (Primary Key, Required)
  - `application_number`: String (Required, Unique human-readable identifier)
  - `applicant_id`: UUID (Foreign Key, Required)
  - `scheme_id`: UUID (Foreign Key, Required)
  - `scheme_version_id`: UUID (Foreign Key, Required, Immutable Reference)
  - `status`: Enum (`DRAFT`, `SUBMITTED`, `UNDER_REVIEW`, `DEFICIENCY`, `RESUBMITTED`, `VERIFIED`, `APPROVED`, `REJECTED`)
  - `submitted_at`: Timestamp (Optional, Set upon submission)
  - `assigned_officer_id`: UUID (Optional, Foreign Key to `users.id`)

### 1.3 Scheme & Scheme Version Entities
- **Source of Truth:** Official Ministry Gazette / Statutory Guidelines (`tribal.nic.in`)
- **Sensitive Classification:** Public Reference Data
- **Fields:**
  - `id`: UUID (Primary Key, Required)
  - `code`: String (Unique, e.g. `"NFST"`, `"TOPCLASS"`, `"NOS"`)
  - `title`: String (Required)
  - `version_number`: Integer (Required, Sequential)
  - `is_active`: Boolean (Required, Only one active version per scheme)
  - `rules`: JSON / Related Records (Deterministic income, age, qualification thresholds)
  - `source_url`: String (Required, Authoritative government URL)
  - `publication_date`: Date (Required)

### 1.4 Document Entity
- **Source of Truth:** Citizen Upload (Attested by Scrutiny Officer)
- **Sensitive Classification:** Confidential / PII Document
- **Fields:**
  - `id`: UUID (Primary Key, Required)
  - `application_id`: UUID (Foreign Key, Required)
  - `document_type`: Enum (`INCOME_CERTIFICATE`, `CASTE_CERTIFICATE`, `MARK_SHEET`, `ADMISSION_LETTER`, `DISABILITY_CERTIFICATE`)
  - `file_storage_key`: UUID (Required, Path on disk/S3; original filename stripped)
  - `mime_type`: String (Required, Verified magic bytes: `application/pdf`, `image/png`, `image/jpeg`)
  - `file_size_bytes`: Integer (Required, Max 5,242,880 bytes / 5MB)
  - `sha256_checksum`: String (Required, Cryptographic hash)
  - `malware_scan_status`: Enum (`PENDING`, `CLEAN`, `INFECTED`, `UNAVAILABLE`)

### 1.5 Eligibility Result Entity
- **Source of Truth:** MoTA Deterministic Rule Engine (`RuleEngineService`)
- **Sensitive Classification:** Official System Evaluation (100% Deterministic)
- **Fields:**
  - `scheme_version_id`: UUID (Required)
  - `is_eligible`: Boolean (Required)
  - `rules_passed`: List of rule IDs (Required)
  - `rules_failed`: List of rule IDs with statutory failure rationales (Required)
  - `evaluation_timestamp`: Timestamp (Required)

---

## 2. Final Data-Contract Matrix (Phase 17 Requirement)

| Entity | Source of Truth | External Sharing Allowed | Sensitivity Level | Audit Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **Applicant Profile** | MoTA Application Portal | Strictly Authorized Only (Masked) | Confidential / PII | Logged on every read/update |
| **Application** | MoTA Application Service | Authorized Nodal Agencies Only | Official Internal | Full lifecycle state transition audit |
| **Scheme** | Official Ministry Gazette | Unrestricted Public Read | Public Reference | Published/Archived audit trail |
| **Scheme Version** | Statutory Guideline Rules | Unrestricted Public Read | Public Reference | Immutability audit verified |
| **Document** | Citizen Upload & Storage | Strictly Gated; No Direct URLs | Confidential / PII | Logged on upload, scan, and download |
| **Eligibility Result**| Deterministic Rule Engine | Applicant & Scrutiny Officer | Official System | Evaluated rules and outcomes recorded |
| **Case & Notes** | Scrutiny Officer | Internal Officers Only | Official Internal | Logged on note creation and assignment |
| **Notification** | Notification Service | Intended Recipient Citizen | Confidential User | Delivery and read timestamp tracked |
| **Gov Verification** | Government Integration | Authorized Officers / Audit | High Sensitivity | Token, status, and adapter tracked |
| **Audit Event** | Security & Workflow Events| Super Admin & Auditors Only | Tamper-Evident High | Immutable append-only log |
