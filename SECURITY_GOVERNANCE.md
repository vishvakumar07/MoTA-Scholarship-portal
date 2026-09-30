# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Institutional Security Governance & Risk Management Policy

> **Classification:** Enterprise Information Security Policy  
> **Status:** APPROVED POLICY (Phase 16)  
> **Notice:** Formal third-party CERT-In audit certification is: `PENDING FORMAL INSTITUTIONAL ENGAGEMENT`.

---

## 1. Information Security Governance Roles

- **Chief Information Security Officer (CISO):** Overall institutional accountability for risk management, regulatory compliance, and incident escalation.
- **Security Operations (SecOps) Lead:** Daily monitoring of `audit_logs`, anomaly detection, rate-limiting tuning, and virus signature updates.
- **Application Security Lead:** Code security reviews, CI SAST/DAST pipeline enforcement, dependency vulnerability remediation.
- **Database Administrator (DBA):** Database credential rotation, least-privilege user enforcement, encrypted tablespace management.

---

## 2. Privileged Access Governance (PAM)

1. **Zero Shared Accounts:** Administrative actions must be performed by individually authenticated users with explicit roles (`super_admin`, `scheme_admin`).
2. **Database User Least Privilege:** The application connects to PostgreSQL using `mota_app_user` with restricted DML permissions (`SELECT`, `INSERT`, `UPDATE`). Direct `DROP`, `ALTER`, or `TRUNCATE` permissions are blocked in production.
3. **Emergency Access ("Break-Glass"):** Direct production database access requires dual authorization and generates mandatory security audit alerts.
