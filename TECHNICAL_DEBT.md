# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Technical Debt Register & Long-Term Engineering Backlog

> **Classification:** Engineering Governance & Backlog Tracking  
> **Status:** AUDITED BASELINE (Phase 16)  
> **Policy:** Technical debt items must be backed by real architectural evidence.

---

## Technical Debt Register

| ID | Component | Problem Description | Impact & Architectural Risk | Priority | Suggested Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TD-01** | Deployment Host | System runs on single-node local/staging host. | Host hardware failure causes service outage. | **HIGH** | Commission multi-node sovereign cloud infrastructure (NIC MeghRaj / SDC). |
| **TD-02** | Government Adapters | Adapters currently operate in STUB mode. | Real Aadhaar, DigiLocker, and PFMS verification not live. | **HIGH** | Execute bilateral institutional MoUs and configure live mTLS gateway credentials. |
| **TD-03** | Monitoring | Host Prometheus & Grafana agents not active on host. | System metrics require manual log inspection. | **MEDIUM**| Deploy node exporters and Prometheus scrapers on institutional host. |
| **TD-04** | Notification Dispatch | Outbound email and SMS in simulated delivery mode. | Citizens must log in to portal to check notification status. | **MEDIUM**| Connect institutional SMTP relay (`aiosmtplib`) and CDAC Mobile Seva gateway. |
| **TD-05** | Virus Definitions | ClamAV signatures require manual/offline update in air-gap.| Potential gap in zero-day malware detection. | **LOW** | Configure automated scheduled offline `freshclam` mirror synchronization. |
