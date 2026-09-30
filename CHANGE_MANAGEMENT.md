# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Production Change Management & Release Governance Policy

> **Classification:** SRE & DevOps Change Governance  
> **Status:** APPROVED OPERATIONAL SPECIFICATION (Phase 15)  
> **Mandate:** Zero-Downtime Planning, Traceable Commits, Peer Review, Mandatory Rollback Procedures

---

## 1. Change Classification & Approval Gates

| Change Type | Definition | Risk Level | Required Approvals | Testing Gate | Deployment Window |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Standard Change** | Pre-approved, routine updates (e.g. ClamAV signature updates, minor doc edits). | Low | DevOps Lead | Automated CI pass | Any business hour |
| **Normal Change** | Code release, new UI components, dependency updates, non-breaking migrations. | Medium | Tech Lead + QA Lead | Full regression (101 tests) + Staging smoke test | Off-peak hours |
| **Major Change** | Database schema refactoring, auth model update, external government gateway activation. | High | Change Advisory Board (CAB) + MoTA Directorate | Full regression + Staging UAT + Backup verification | Scheduled maintenance window |
| **Emergency Change** | Urgent hotfix for P0 incident, active vulnerability remediation, or data breach containment. | Critical | Incident Commander + Lead Architect | Accelerated test pass + Peer sign-off | Immediate with post-implementation review |

---

## 2. Standard Change Request (CR) Workflow

```text
[Change Request Created]
         │
         ▼
[Technical & Risk Review] ──> (Rejected / Rework)
         │
         ▼
[Staging Validation & Automated Regression (101/101 Passed)]
         │
         ▼
[Change Advisory Board (CAB) Approval]
         │
         ▼
[Pre-Deployment Database Backup Verified]
         │
         ▼
[Production Deployment Execution]
         │
         ├─> (Deployment Success) ──> [Post-Deployment Smoke Test] ──> [Change Closed]
         │
         └─> (Deployment Failure) ──> [Trigger Immediate Rollback] ──> [Post-Mortem Review]
```

---

## 3. Rollback Triggers & Execution Criteria

A deployment must be rolled back immediately if any of the following occur within 60 minutes post-launch:
1. Elevated 5xx HTTP error rate exceeding 1.0% on core API endpoints.
2. Inability to execute user authentication (login/registration failures).
3. Failure in deterministic eligibility evaluation or application submission.
4. Document upload or virus scanning pipeline failure.
5. Database deadlock or transaction rollback rate exceeding 0.5%.

Rollback execution follows [PRODUCTION_RUNBOOK.md](file:///E:/MoTA%20Scholarship/PRODUCTION_RUNBOOK.md) Section 16.
