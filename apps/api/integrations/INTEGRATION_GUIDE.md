# Phase 7: Government Integration Readiness Framework

## Overview

This document describes the Government Integration Adapter Framework implemented in Phase 7 of the MoTA Scholarship & Fellowship Management System.

---

## 1. Which Integrations Are Supported

| Integration | Adapter Class | Current Mode | Status |
|-------------|--------------|--------------|--------|
| UIDAI (Aadhaar) | `UIDaiAdapter` | `stub` | Not Configured |
| DigiLocker | `DigiLockerAdapter` | `stub` | Requires Authorized Access |
| National Scholarship Portal | `NSPAdapter` | `stub` | Not Configured |
| DBT / Tribal DBT | `DBTAdapter` | `stub` | Not Configured |
| MoTA Dashboard / Ministry | `MoTAAdapter` | `stub` | Not Configured |
| Mock (Testing Only) | `MockGovernmentIntegrationAdapter` | test | Never in production |

---

## 2. Which Integrations Are Currently Configured

**None.** All integrations are in `stub` mode (default).

No authorized government API credentials have been provided. All operations return truthful `INTEGRATION_NOT_CONFIGURED` or `REQUIRES_AUTHORIZED_ACCESS` status.

---

## 3. Which Integrations Require Authorization

All integrations require authorization from their respective authority:

- **UIDAI (Aadhaar)**: Requires e-KYC authorization from UIDAI. Contact MoTA IT Division.
- **DigiLocker**: Requires OAuth2 client credentials from DigiLocker. Requires Data Processing Agreement.
- **NSP**: Requires API specification and credentials from National Scholarship Portal team.
- **DBT**: Requires authorized access from DBT Mission / NIC. Read-only status check only.
- **MoTA**: Requires official API specification from MoTA IT Division.

---

## 4. Required Credentials / Configuration

Set in `.env` (never commit real values):

```bash
# UIDAI
AADHAAR_INTEGRATION=stub   # Change to "live" only with authorized credentials
UIDAI_ENABLED=false
UIDAI_BASE_URL=
UIDAI_CLIENT_ID=
# UIDAI_CLIENT_SECRET=   (backend-only)

# DigiLocker
DIGILOCKER_INTEGRATION=stub
DIGILOCKER_ENABLED=false
DIGILOCKER_BASE_URL=
DIGILOCKER_CLIENT_ID=
# DIGILOCKER_CLIENT_SECRET=   (backend-only)

# NSP
NSP_INTEGRATION=stub
NSP_ENABLED=false
NSP_BASE_URL=
NSP_CLIENT_ID=

# DBT
DBT_INTEGRATION=stub
DBT_ENABLED=false
DBT_BASE_URL=
DBT_CLIENT_ID=

# MoTA
MOTA_DASHBOARD_INTEGRATION=stub
MOTA_ENABLED=false
MOTA_BASE_URL=
MOTA_CLIENT_ID=
```

**SECURITY**: `CLIENT_SECRET`, `API_KEY`, `ACCESS_TOKEN`, `REFRESH_TOKEN`, `PRIVATE_KEY` must NEVER be exposed to the browser, logged, or returned in API responses.

---

## 5. Security Model

- All government credentials are **backend-only** environment variables.
- Secrets are **never** returned in API responses.
- Secrets are **never** logged (not even at DEBUG level).
- Authorization headers are **never** logged.
- Raw government API response payloads are **never** stored in the database.
- Only minimal normalized result + reference IDs are retained.

---

## 6. Adapter Architecture

```
Applicant / Officer
      ↓
MoTA Application API (FastAPI)
      ↓
routers/integrations.py       ← RBAC enforcement
      ↓
integrations/service.py       ← Rate limiting, idempotency, error containment
      ↓
integrations/adapters.py      ← Concrete adapter (UIDaiAdapter, etc.)
      ↓
integrations/base.py          ← Abstract base, GovIntegrationResponse contract
      ↓
Authorized Government API     ← Only when mode=live + credentials configured
```

---

## 7. Response States

| Status | Meaning |
|--------|---------|
| `SUCCESS` | Authorized integration returned a positive result |
| `NOT_VERIFIED` | Integration ran but could not verify the record |
| `REQUIRES_AUTHORIZED_ACCESS` | OAuth/credentials required (DigiLocker pattern) |
| `INTEGRATION_NOT_CONFIGURED` | Credentials/config absent |
| `TEMPORARILY_UNAVAILABLE` | Configured but endpoint unreachable |
| `UNSUPPORTED_OPERATION` | Adapter does not implement this operation |
| `DISABLED` | Explicitly disabled in config |
| `ERROR` | Unexpected failure (rate limit, timeout, etc.) |

**PROHIBITED STATUS VALUES (must never appear):**
- `VERIFIED` (as a status — only `verified=True` field on SUCCESS responses from live authorized APIs)
- `AI_VERIFIED`
- `OCR_VERIFIED`
- `AUTO_VERIFIED`

---

## 8. Verification Lifecycle

```
Application Created
      ↓
Officer Reviews Documents (Phase 5 — OCR/AI assistive)
      ↓
Officer Triggers Government Verification (Phase 7)
      ↓
Integration Adapter Called
      ↓
Response Stored in government_verifications table
      ↓
Attempt Recorded in government_verification_attempts table
      ↓
Audit Log Entry Created (no secrets logged)
      ↓
Officer Reviews Result (verified=true/false/null)
      ↓
Officer Makes Final Decision (not the integration)
```

**Government verification is separate from:**
- AI document classification
- OCR text extraction
- Officer manual verification (`DocumentVerificationResult`)
- Application eligibility (`EligibilityResult`)
- Selection decisions (`SelectionResult`)

---

## 9. How to Add a New Government Integration

1. Create a new adapter class in `apps/api/integrations/adapters.py` extending `GovernmentIntegrationAdapter`.
2. Implement `health_check()` and any relevant operations.
3. All unsupported operations must call `self._unsupported(operation)`.
4. Add the new integration to `GovernmentIntegrationService._adapters`.
5. Add configuration in `apps/api/config.py` (mode, base URL, client ID).
6. Add environment variable entries to `.env.example` (no real values).
7. Add the new `IntegrationName` and `GovIntegrationName` enum values.
8. Register the migration if a new DB column is needed.
9. Add tests in `test_gov_integrations.py`.
10. Document in this file.

---

## 10. How to Test Without Contacting Government Systems

Use the `MockGovernmentIntegrationAdapter`:

```python
from integrations.adapters import MockGovernmentIntegrationAdapter

mock = MockGovernmentIntegrationAdapter(configured=True)
result = await mock.verify_identity({"aadhaar_hash": "TEST-HASH-000"})
# result.status == GovIntegrationStatus.SUCCESS
# result.verified == None  ← mock NEVER sets verified=True
# result.message contains "DEMO / TEST -- NOT GOVERNMENT DATA"
```

In tests, instantiate `GovernmentIntegrationService(use_mock=True)` to use mock adapters for all integrations.

**Important**: `MockGovernmentIntegrationAdapter` must NEVER be enabled in production configuration.

---

## 11. Known Limitations

1. Rate limiting uses in-memory state; will reset on server restart. Production should use Redis.
2. Idempotency cache is in-memory (60-second TTL). Production should use Redis or DB.
3. No live government API is connected at this time.
4. DigiLocker OAuth2 authorization flow UI is not yet implemented.
5. Government verification results are not yet surfaced in the main application status workflow.
6. No automatic retry with backoff is implemented (by design — prevents accidental duplicate government requests).

---

## 12. Exact Requirements from MoTA / Government Authorities for Live Integration

### UIDAI (Aadhaar)
- Authorization letter from UIDAI for e-KYC access
- Client ID and client secret from UIDAI Developer Portal
- UIDAI sandbox/production API specification
- Data Processing Agreement (DPA)
- Compliance with UIDAI Authentication API 2.5

### DigiLocker
- OAuth2 client credentials from DigiLocker Developer Portal
- Pull document API specification
- User consent flow implementation
- DigiLocker partner agreement

### National Scholarship Portal
- API specification from NSP/NIC team
- Formal MOU between MoTA and NSP
- Authentication credentials (API key or OAuth)

### DBT Mission
- Formal request to DBT Mission / NIC
- Read-only disbursement status API access
- Authentication credentials

### MoTA Dashboard / Ministry System
- Internal MoTA IT Division project coordination
- Official API endpoint specification
- Access credentials from MoTA IT Division
