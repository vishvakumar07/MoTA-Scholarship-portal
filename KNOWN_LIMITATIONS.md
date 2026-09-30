# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Verified System Limitations & Technical Boundaries

> **Classification:** Technical Transparency & Operational Boundaries  
> **Status:** VERIFIED BASELINE (Phase 13)  
> **Audience:** DevOps Engineers, Security Auditors, Institutional Decision Makers  
> **Policy:** All limitations are recorded transparently without omission.

---

## 1. External Government Integration Status

| Integration Subsystem | Current State | Operational Limitation | Path to Live Production |
| :--- | :--- | :--- | :--- |
| **UIDAI / Aadhaar e-KYC** | `STUB` | Returns simulated OTP / verification status with mock tokens. Real Aadhaar verification is disabled. | Requires authorized AUA/KUA license, HSM signing key, and official UIDAI endpoint configuration. |
| **DigiLocker Integration** | `STUB` | Mock document pull and verification. Live DigiLocker API is not connected. | Requires DigiLocker partner registration, Client ID/Secret, and OAuth2 redirect callback setup. |
| **National Scholarship Portal (NSP)** | `STUB` | Returns de-duplication check stubs. Live cross-portal query is disabled. | Requires official NIC/NSP API access credentials and secure VPN/gateway tunnel. |
| **Direct Benefit Transfer (DBT) / PFMS** | `STUB` | Simulated disbursement push and batch UTR creation. No real banking network connection. | Requires PFMS institutional onboarding, Public Financial Management System credentials, and digital signature tokens. |
| **MoTA Central Database** | `STUB` | Simulates official legacy scholar database reconciliation. | Requires MoTA internal database gateway clearance and secure institutional network access. |

---

## 2. Infrastructure & Deployment Limitations

### 2.1 Single-Node Architecture
- **Current State:** The default Docker Compose setup deploys all containers (Web, API, Celery Worker, PostgreSQL, Redis, ClamAV) on a single physical or virtual host.
- **Limitation:** A host-level failure impacts all services. No multi-node clustering or Kubernetes manifests are bundled in the core repository.
- **Production Path:** Institutional deployment requires migrating PostgreSQL to a managed HA cluster and deploying API/Worker containers across multi-node orchestrators (e.g., Kubernetes / Docker Swarm).

### 2.2 Zero-Downtime Deployment
- **Current State:** `NOT CONFIGURED`.
- **Limitation:** Restarting containers during a production upgrade causes a brief service interruption (typically 10–30 seconds) while new images initialize.
- **Production Path:** Implementation of blue/green or rolling deployment strategies via a production reverse proxy or ingress controller.

### 2.3 Web Application Firewall (WAF) & DDoS Mitigation
- **Current State:** `NOT CONFIGURED` in source control.
- **Limitation:** Application-level rate limiting (`FastAPI-Limiter`) is active, but network-layer volumetric DDoS protection and deep packet WAF inspection must be provided by institutional edge infrastructure (e.g., Cloudflare, AWS WAF, or NIC Sovereign Gateway).

---

## 3. Communication & Notification Dispatch

- **SMS Delivery:** `STUB / SIMULATED`. SMS messages are logged to database notifications and server stdout. No paid commercial SMS gateway (e.g., CDAC Mobile Seva / Twilio) is configured.
- **Email Delivery:** Configured for standard SMTP (`aiosmtplib`). In pilot/local environments without an active SMTP server, notification delivery defaults to database-persisted notifications. Real outbound delivery requires valid institutional SMTP credentials (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`).

---

## 4. Antivirus Definitions & Security Maintenance

- **ClamAV Engine:** The included ClamAV container scans all uploaded files for known malware signatures.
- **Limitation:** In an air-gapped or network-restricted environment, the ClamAV daemon cannot automatically execute `freshclam` to pull updated daily virus signature definitions.
- **Operational Requirement:** The institutional security team must establish a scheduled job to mirror and inject offline virus definition updates (`daily.cvd`, `main.cvd`).

---

## 5. Secret & Cryptographic Key Management

- **Environment Injection:** Secrets are read from environment variables or Docker `.env` files.
- **Limitation:** Native integration with hardware security modules (HSM) or dynamic secret managers (HashiCorp Vault / AWS Secrets Manager) is architected via standard environment variable abstraction but requires external agent injection in production.
- **Key Rotation:** Rotating `FIELD_ENCRYPTION_KEY` requires executing a custom re-encryption database script to re-encrypt existing encrypted columns.


---

## 6. Phase 15 Operational Monitoring & Production Host Status

- **Production Cloud Host:** `NO PRODUCTION ENVIRONMENT`. The system is currently validated and benchmarked on local testing and staging environments. Live government cloud hosting (NIC MeghRaj / SDC) has not yet been provisioned.
- **Live Monitoring Infrastructure:** Prometheus and Grafana operational dashboards are instrumented in code, but live metrics scraping agents are `NOT CONFIGURED` until sovereign host infrastructure is provisioned.
- **Production Operational Data:** All operational metrics and performance numbers reflect real, measured local benchmarks. Zero production citizen records or live government transactions exist.
