# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# API Architecture & Integration Governance Specification

> **Classification:** Enterprise API Governance Framework  
> **Status:** APPROVED SPECIFICATION (Phase 16)  
> **Scope:** Internal Services, Officer Portals, and Authorized Institutional Gateways

---

## 1. API Versioning & Lifecycle Policy

1. **URL-Based Versioning:** All public endpoints follow the structured path prefix: `/api/v{major}/` (Current baseline: `/api/v1/`).
2. **Backward Compatibility Guarantee:** Existing endpoints within `/api/v1/` will not introduce breaking changes (e.g. removing fields, altering data types, or enforcing new required parameters).
3. **Deprecation Protocol:** If an endpoint must be deprecated:
   - Mark endpoint with OpenAPI `@app.get(..., deprecated=True)`.
   - Return standard HTTP header: `Deprecation: @<timestamp>`.
   - Provide minimum **12-month deprecation notice** before sunsetting.
4. **Breaking Changes:** Any breaking contract modification requires introducing `/api/v2/`.

---

## 2. Authentication, Authorization & Security Standards

- **Bearer Token Authentication:** Access tokens are signed JWTs (HS256 or RS256 in institutional PKI) with a strict **15-minute expiration window**.
- **Role-Based Scope Guards:** Every endpoint enforces least-privilege RBAC dependencies (`require_roles(...)`).
- **No Sensitive Data in URLs:** API paths and query parameters must never contain passwords, tokens, Aadhaar numbers, or bank account numbers.
- **Rate Limiting:** Global and endpoint-specific sliding-window rate limiting active on `/auth/login`, `/auth/register`, and `/documents/upload`.
- **Idempotency:** State-modifying requests (`POST /applications`, `POST /cases/action`) support `Idempotency-Key` headers to prevent duplicate operations.

---

## 3. Standard Response & Error Envelope (RFC 7807 Inspired)

All error responses adhere to a consistent JSON structure:

```json
{
  "detail": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested application does not exist or access is unauthorized.",
    "correlation_id": "req-9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "timestamp": "2026-09-28T10:30:00Z"
  }
}
```
