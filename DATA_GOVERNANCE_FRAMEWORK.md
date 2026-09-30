# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Enterprise Data Governance, Quality & Lineage Framework

> **Classification:** Sovereign Data Governance Framework  
> **Compliance Target:** Digital Personal Data Protection Act (DPDPA), 2023 / IT Act, 2000  
> **Core Mandate:** Data Minimization, Cryptographic Protection, Purpose Limitation, Immutable Audit

---

## 1. Complete Data Classification & Ownership Matrix

| Data Classification | Managed Entities | Storage Subsystem | Institutional Owner | Retention Status | Deletion Protocol |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Public / Reference** | Schemes, eligibility criteria, guidelines, versions. | PostgreSQL `schemes` | MoTA Scheme Directorate | Permanent | Archival only; deletion prohibited |
| **2. Applicant Personal (PII)**| Name, DOB, caste, income, disability, bank details. | PostgreSQL `users`, `applicant_profiles` | Applicant (Data Principal) | Active Award + Audit period (`OFFICIAL INFO REQUIRED`) | Pseudonymization on verified erasure request |
| **3. Identity (Aadhaar)** | SHA-256 hash of 12-digit UID. **Raw UID never stored.** | PostgreSQL `users.aadhaar_hash` | Security / Identity Nodal Officer | Tied to user account lifecycle | Erased upon account decommissioning |
| **4. Sensitive Documents** | Caste/income certificates, marksheets, disability certs. | Local storage / S3 (`StorageService`) | Document Scrutiny Directorate | Active sanction + verification audit | Cryptographic file shredding / bucket lifecycle |
| **5. AI & OCR Extractions** | Extracted text, quality confidence scores, flags. | PostgreSQL `document_extractions` | AI Governance Officer | Advisory lifecycle (Tied to parent doc) | Purged with parent document |
| **6. Operational & Cases** | Work queues, deficiency notices, scrutiny remarks. | PostgreSQL `cases`, `deficiency_notices` | Operations / Scrutiny Directorate | 7 years administrative record | Archived per institutional record policy |
| **7. Security & Audit Logs** | Authentication events, state changes, access traces. | PostgreSQL `audit_logs` (Append-only) | Chief Information Security Officer | Minimum 7 years (Statutory archive) | Deletion strictly prohibited |

---

## 2. Data Lineage & Provenance Architecture

The platform enforces strict provenance tracing across the application lifecycle:

```text
[Applicant Input] ──> [Deterministic Rule Engine] ──> [Application Record Created]
         │                          │                               │
         │                          ▼                               ▼
         │                 [Eligibility Result]          [Encrypted Storage]
         │                          │                               │
         ▼                          │                               ▼
[Uploaded Document] ──────> [ClamAV Antivirus] ────────> [Advisory OCR/AI]
         │                          │                               │
         └──────────────────────────┼───────────────────────────────┘
                                    │
                                    ▼
                      [Officer Scrutiny Workbench]
                                    │
                                    ▼
                      [Official Sanction / Outcome]
                                    │
                                    ▼
                      [Append-Only Tamper-Evident Audit]
```

- **Data Attribution Guarantee:** Every field displayed in the Scrutiny Workbench is explicitly tagged with its origin (`Applicant Submitted`, `Advisory AI Extracted`, or `Official Officer Entered`). Advisory AI data is visually distinguished and never presented as official truth.
