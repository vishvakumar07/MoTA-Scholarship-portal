# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Integration Sandbox & Simulation Environment Guide

> **Classification:** Developer & Partner Integration Guide  
> **Status:** APPROVED SPECIFICATION (Phase 17)  
> **Mandatory Notice:** `SANDBOX / TEST — NOT GOVERNMENT DATA. SIMULATED RESPONSES ONLY.`

---

## 1. Sandbox Purpose & Boundaries

The MoTA Sandbox environment enables authorized partner institutions (e.g. state tribal welfare departments, universities) to validate API integrations without touching production systems or processing real citizen data:
1. **Isolated Database:** Completely separate database instance (`mota_sandbox_db`) with synthetic test schemes and test applicants.
2. **Explicit Simulated Labels:** All sandbox responses include standard metadata headers and JSON markers:
   ```json
   {
     "_sandbox": true,
     "_notice": "SIMULATED ADVISORY TEST DATA - NOT OFFICIAL GOVERNMENT VERIFICATION",
     "status": "REQUIRES_AUTHORIZED_ACCESS"
   }
   ```
3. **Zero Production Credential Sharing:** Sandbox environments use isolated test secrets. Production JWT keys or encryption keys are never deployed to sandbox.
4. **Zero Live Gateway Calls:** External government integrations execute entirely within local mock adapters (`MockIntegrationAdapter`), ensuring zero traffic reaches live UIDAI or PFMS networks.

---

## 2. Testing Synthetic Verification Scenarios

| Test Case Code | Purpose | Expected Status |
| :--- | :--- | :--- |
| `TEST-UIDAI-01` | Simulate unconfigured Aadhaar verification | `REQUIRES_AUTHORIZED_ACCESS` (Mock token generated, verified: false) |
| `TEST-DIGI-01` | Simulate certificate verification query | `REQUIRES_AUTHORIZED_ACCESS` (Advisory mock returned) |
| `TEST-RATE-01` | Exceed rate limit on verification endpoint | `429 Too Many Requests: Rate limit exceeded` |
| `TEST-IDOR-01` | Attempt accessing another applicant's sandbox case | `404 Not Found` / `403 Forbidden` |
