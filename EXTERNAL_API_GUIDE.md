# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# External Institutional API Reference & Integration Guide

> **Classification:** Technical Integration Reference  
> **Status:** APPROVED SPECIFICATION (Phase 17)  
> **Audience:** Authorized Institutional Partners (State Directorates, Central Repositories)

---

## 1. Overview & Authentication

Authorized institutional systems communicate with the MoTA platform via secure RESTful APIs:
- **Base URL:** `https://api.scholarships.mota.gov.in/api/v1`
- **Transport Security:** Mandatory TLS 1.3 / HTTPS.
- **Authentication:** OAuth 2.0 Client Credentials or institutional Bearer JWT tokens.
- **Header Requirements:**
  - `Authorization: Bearer <INSTITUTIONAL_TOKEN>`
  - `X-Request-ID: <UUID>` (Client correlation identifier)
  - `Content-Type: application/json`

---

## 2. Authorized Institutional Endpoints

### 2.1 Scheme Catalogue Discovery
- **Endpoint:** `GET /api/v1/schemes`
- **Purpose:** Retrieve active statutory MoTA scholarship and fellowship schemes.
- **Access:** Public / Institutional Read.
- **Response Example:**
  ```json
  [
    {
      "code": "NFST",
      "title": "National Fellowship for Higher Education of ST Students",
      "type": "Central Sector",
      "active_version": 1,
      "source_url": "https://tribal.nic.in/ScholarshiP.aspx"
    }
  ]
  ```

### 2.2 Scheme Version Rules & Criteria
- **Endpoint:** `GET /api/v1/schemes/{code}`
- **Purpose:** Inspect deterministic eligibility rules and income thresholds for a specific scheme.
- **Access:** Public / Institutional Read.

### 2.3 Application Eligibility Pre-Check
- **Endpoint:** `POST /api/v1/applications/eligibility-check`
- **Purpose:** Submit candidate attributes (caste, income, marks) to receive deterministic eligibility outcome before application creation.
- **Access:** Authenticated Institutional / Citizen.
- **Rate Limit:** 30 requests/minute.

### 2.4 Privacy-Preserving Analytical Metrics
- **Endpoint:** `GET /api/v1/admin/analytics/schemes`
- **Purpose:** Fetch aggregated application volume and verification metrics without exposing individual applicant PII.
- **Access:** Authorized Institutional Officer / Administrator (`require_roles("scheme_admin", "super_admin")`).
