# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Long-Term Architecture Evolution Plan

> **Classification:** Enterprise Architectural Strategy  
> **Status:** RATIFIED BASELINE (Phase 16)  
> **Core Principle:** Evidence-Driven Evolution; Modular Monolith Preservation; No Microservices Creep

---

## 1. Architectural Component Evolution Matrix

Every subsystem is evaluated and assigned a long-term classification:

| Subsystem Component | Classification | Justification & Architectural Evidence | Target Evolutionary Path |
| :--- | :--- | :--- | :--- |
| **Frontend Web (`apps/web`)** | `KEEP` | Next.js 14 App Router provides optimal SSR performance, accessible UI, and clean TypeScript boundaries. | Maintain current architecture. Optimize asset caching via institutional CDN/WAF. |
| **Backend API (`apps/api`)** | `KEEP` | FastAPI modular monolith provides sub-millisecond routing, clean service/repository boundaries, and low operational overhead. | Retain modular monolith. Resist microservices decomposition without proven organizational scaling need. |
| **Relational DB (PostgreSQL 16)** | `OPTIMIZE` | PostgreSQL 16 with pgvector handles relational integrity and semantic search effortlessly. | Scale vertically first; implement read replicas for heavy analytical dashboards only if query volume exceeds 1,000 QPS. |
| **Task Queue (Celery + Redis)** | `KEEP` | Celery effectively isolates heavy I/O (ClamAV scans, OCR extraction, email notifications). | Scale workers horizontally by adding container replicas across the private Redis broker. |
| **Storage (`StorageService`)** | `KEEP` | Interface cleanly decouples application logic from physical disk. | Maintain local storage for development/pilot; switch `STORAGE_BACKEND=s3` for sovereign cloud storage. |
| **Deterministic Rule Engine** | `KEEP` | 100% deterministic Python rules execute in 25.45 µs. Essential for legal defensibility. | Never replace with AI. Maintain statutory traceability and version immutability. |
| **AI / OCR Subsystem** | `KEEP` | Pluggable interface enforces strict advisory boundaries. | Maintain fail-open behavior; evaluate sovereign on-premise LLMs (e.g. Indic-BERT / Tesseract) for air-gapped nodes. |
| **Government Adapters** | `OPTIMIZE` | Adapter contracts are certified in STUB mode with honest boundaries. | Implement mTLS client certificates and OAuth2 flows upon formal bilateral MoU execution. |
| **Microservices Decomposition** | `DEFER` | Current traffic patterns and operational complexity do not justify distributed network overhead or distributed transactions. | Re-evaluate only if multiple independent ministry directorates require isolated release cycles. |
| **Kubernetes Orchestration** | `DEFER` | Docker Compose / Docker Swarm is sufficient for single-host or clustered sovereign VMs. | Adopt Kubernetes only if institutional host infrastructure mandates it as the sovereign standard. |
