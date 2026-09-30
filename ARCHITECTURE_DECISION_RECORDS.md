# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Architecture Decision Records (ADRs)

> **Classification:** Enterprise Architectural History  
> **Status:** RATIFIED BASELINE (Phases 1–16)

---

### ADR-001: Local-First, Docker-First Prototype Architecture
- **Context:** Need for a reproducible, zero-cost, air-gap-capable development and evaluation environment for Smart India Hackathon.
- **Decision:** Build as a local-first system with zero mandatory paid cloud dependencies (AWS, GCP, Azure).
- **Status:** **Accepted & Preserved**.

### ADR-002: PostgreSQL 16 + pgvector as Primary Relational Store
- **Context:** Need for strict relational ACID compliance, foreign key cascades, and vector semantic similarity.
- **Decision:** Use PostgreSQL with pgvector extension instead of separate document or vector databases.
- **Status:** **Accepted & Preserved**.

### ADR-003: Celery + Redis for Asynchronous Task Processing
- **Context:** Heavy I/O (malware scanning, OCR, notifications) must not block HTTP request threads.
- **Decision:** Use Celery with Redis task broker and password-protected authentication.
- **Status:** **Accepted & Preserved**.

### ADR-004: Pluggable StorageService Abstraction
- **Context:** Need to support local disk during pilot, and sovereign S3 object storage in production.
- **Decision:** Abstract all file storage operations behind `StorageService` interface.
- **Status:** **Accepted & Preserved**.

### ADR-005: Pluggable AIService with Assistive-Only Boundary
- **Context:** Cloud AI services may fail, lack connectivity, or exceed quotas.
- **Decision:** Implement `AIService` with `MOCK`, `GEMINI`, `LOCAL`, and `UNAVAILABLE` modes. AI is strictly assistive.
- **Status:** **Accepted & Preserved**.

### ADR-006: Gated Government Integration Adapter Architecture
- **Context:** Government APIs require bilateral MoUs and licenses (AUA/KUA) unavailable during development.
- **Decision:** Implement adapters with strict `STUB` default returning honest `REQUIRES_AUTHORIZED_ACCESS`. Zero fabrication.
- **Status:** **Accepted & Preserved**.

### ADR-007: Statutory Scheme Version Immutability
- **Context:** Scholarship rules change across academic years; historical applications must remain legally defensible.
- **Decision:** Published scheme versions are immutable. Applications permanently reference their submission version ID.
- **Status:** **Accepted & Preserved**.

### ADR-008: Deterministic Rule Engine as Sole Eligibility Authority
- **Context:** Public funds allocation requires legally binding, reproducible eligibility determination.
- **Decision:** Codify rules in Python (`RuleEngineService`); 100% deterministic evaluation. AI never decides eligibility.
- **Status:** **Accepted & Preserved**.

### ADR-009: Human Officer Administrative Decision Authority
- **Context:** Discretionary administrative decisions require constitutional accountability.
- **Decision:** All official actions (verification, deficiency, sanction, rejection) must be performed by authenticated human officers.
- **Status:** **Accepted & Preserved**.


### ADR-017: RESTful API Interoperability with Semantic Versioning
- **Context:** Need to allow authorized institutional systems to query schemes and verification statuses without breaking existing clients.
- **Decision:** Expose standardized REST endpoints under `/api/v1/` prefix with strict backward compatibility and minimum 12-month deprecation periods.
- **Status:** **Accepted & Implemented**.

### ADR-018: Canonical Data Contracts with Strict Source-of-Truth Hierarchy
- **Context:** Multi-system data exchange risks data inconsistency and unauthorized overwrites.
- **Decision:** Codify canonical data contracts; enforce clear source-of-truth ownership per field; prohibit external systems from overwriting authoritative citizen or officer data.
- **Status:** **Accepted & Implemented**.

### ADR-019: HMAC-SHA256 Signed Webhook Framework with Replay Defense
- **Context:** Future inbound institutional webhooks require protection against spoofing, tampering, and replay.
- **Decision:** Mandate HMAC-SHA256 signature verification, a 300-second timestamp tolerance window, and idempotent `X-Event-ID` processing.
- **Status:** **Accepted & Implemented**.

### ADR-020: Identity Federation Readiness via OIDC / Jan Parichay Abstraction
- **Context:** Government portals are moving toward unified citizen SSO (Jan Parichay / MeriPehchaan).
- **Decision:** Architect identity federation as a pluggable authentication adapter mapping external claims to internal roles while preserving local fallback.
- **Status:** **Accepted & Implemented**.

### ADR-021: Privacy-Preserving Controlled Bulk Data Exchange
- **Context:** Bulk export of welfare beneficiary data presents high risk of mass surveillance and PII leakage.
- **Decision:** Prohibit unauthenticated bulk exports; restrict operational exports to authorized administrators; mandate field masking and audit logging.
- **Status:** **Accepted & Implemented**.

### ADR-022: Fail-Safe Integration Circuit Breakers & Failure Isolation
- **Context:** Outbound government API failures must never cause cascade failures across the scholarship portal.
- **Decision:** Implement circuit breaker patterns; fail open for assistive services; record honest `REQUIRES_AUTHORIZED_ACCESS` status without fabrication.
- **Status:** **Accepted & Implemented**.
