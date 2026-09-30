# Government Integration Readiness & Adapter Framework

**Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System**  
**SIH Final Submission Document — Technical Integration Specification**

---

## 1. Integration Governance Principles
The MoTA Scholarship Management System incorporates an **Integration-Ready Adapter Architecture**. In strict adherence to government software standards and SIH competition rules:

1. **No Fabricated Connectivity**: The platform never simulates fake government API success, fake Aadhaar OTP validations, or fake PFMS transaction UTRs.
2. **Explicit Readiness States**: Each external adapter exposes its real technical status:
   - `REQUIRES AUTHORIZED GOVERNMENT INTEGRATION`
   - `INTEGRATION DISABLED`
   - `NOT CONFIGURED`
   - `LIVE` (Only when authorized government credentials and endpoints are supplied)

---

## 2. Integration Adapters Inventory

### 2.1 UIDAI / Aadhaar Identity Verification
- **Adapter Class**: `UIDAIAdapter` in `apps/api/integrations/uidai.py`
- **Purpose**: Demographic verification and biometric/OTP e-KYC.
- **Current Mode**: `REQUIRES AUTHORIZED ACCESS` (Disabled by default).
- **Security Control**:
  - Raw Aadhaar numbers are never transmitted to unapproved third parties.
  - One-way SHA-256 hash used locally for applicant record deduplication.
  - No synthetic Aadhaar numbers are ever generated or stored.
- **Activation Prerequisites**:
  - Authorized AUA / KUA (Authentication User Agency) license from UIDAI.
  - Static IP whitelisting and production signing certificates.
  - Set `UIDAI_ENABLED=true`, `UIDAI_BASE_URL`, and credentials in `.env`.

### 2.2 DigiLocker Document Verification
- **Adapter Class**: `DigiLockerAdapter` in `apps/api/integrations/digilocker.py`
- **Purpose**: Direct retrieval of digitally signed ST caste certificates, income certificates, and academic marksheets.
- **Current Mode**: `REQUIRES AUTHORIZED ACCESS` (Disabled by default).
- **Security Control**:
  - OAuth 2.0 PKCE flow architecture prepared for citizen consent-driven document retrieval.
  - Returns `is_verified: False` and `status: requires_authorized_access` until officially provisioned.
- **Activation Prerequisites**:
  - Registered MoTA Requester Client ID on DigiLocker API Portal.
  - Set `DIGILOCKER_ENABLED=true`, `DIGILOCKER_CLIENT_ID`, and `DIGILOCKER_CLIENT_SECRET`.

### 2.3 National Scholarship Portal (NSP) Federation
- **Adapter Class**: `NSPAdapter` in `apps/api/integrations/nsp.py`
- **Purpose**: Cross-portal de-duplication to prevent dual scholarship awards across ministries.
- **Current Mode**: `INTEGRATION DISABLED`.
- **Activation Prerequisites**:
  - National Informatics Centre (NIC) NSP API gateway access token and IP whitelist.

### 2.4 Direct Benefit Transfer (DBT / PFMS)
- **Adapter Class**: `DBTAdapter` in `apps/api/integrations/dbt.py`
- **Purpose**: Scholarship disbursement file creation and payment status tracking via PFMS / APBS.
- **Current Mode**: `INTEGRATION DISABLED`.
- **Integrity Guarantee**:
  - No fake UTR numbers or fake disbursement confirmation receipts are ever created.

### 2.5 Ministry of Tribal Affairs (MoTA) Dashboard
- **Adapter Class**: `MoTADashboardAdapter` in `apps/api/integrations/mota.py`
- **Purpose**: Upstream aggregation of anonymized tribal education metrics for Ministry leadership.
- **Current Mode**: `NOT CONFIGURED / DISABLED`.

---

## 3. Configuration & Activation Workflow
When official credentials are authorization-granted by MoTA / MeitY:

```env
# Example configuration in .env for authorized deployment
UIDAI_ENABLED=true
UIDAI_BASE_URL=https://auth.uidai.gov.in/1.0
UIDAI_CLIENT_ID=your_aua_code

DIGILOCKER_ENABLED=true
DIGILOCKER_BASE_URL=https://digilocker.meripehchan.gov.in/public/oauth2/1
DIGILOCKER_CLIENT_ID=your_client_id
DIGILOCKER_CLIENT_SECRET=your_client_secret
```
