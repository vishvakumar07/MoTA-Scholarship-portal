# SIH Demonstration Guide & Rehearsal Runbook

**Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System**  
**SIH Final Submission Document — Evaluator Demonstration Manual**

---

## 1. Demonstration Overview
This runbook guides evaluators and presenters through a complete, reproducible, end-to-end demonstration of the MoTA Scholarship & Fellowship Management System using **only permitted DEMO/TEST data**.

### Demo Core Tenet
> **TRUTHFUL DEMONSTRATION GUARANTEE**:  
> Every screen displays real, database-driven application data.  
> Unavailable government integrations are truthfully displayed with `REQUIRES AUTHORIZED ACCESS` or `INTEGRATION DISABLED`.  
> No fake government approvals, fake Aadhaar responses, fake bank transactions, or fake citizens are generated.

---

## 2. Environment Startup Options

### Option A: Docker Deployment (Recommended)
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Start all services (Next.js Web, FastAPI, Celery Worker, PostgreSQL, Redis, ClamAV)
docker compose up --build

# 3. In another terminal, apply migrations and seed verified MoTA schemes:
docker compose exec api alembic upgrade head
docker compose exec api python infra/scripts/seed_schemes.py
```

### Option B: Local Direct Execution
```bash
# Terminal 1 - Backend API:
cd "E:\MoTA Scholarship\apps\api"
..\..\.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend Web:
cd "E:\MoTA Scholarship\apps\web"
npm run dev
```

Access points:
- **Frontend Portal**: [http://localhost:3000](http://localhost:3000)
- **Interactive OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 3. Demo Roles & Credentials
Pre-seeded / Demo login accounts for evaluation:

| Role | Email | Purpose |
|---|---|---|
| **Applicant** | `applicant.demo@mota-sih.gov.in` | ST student applicant workflow |
| **Scrutiny Officer** | `officer.demo@mota-sih.gov.in` | Work queue scrutiny, deficiency creation, resolution |
| **Scheme Administrator** | `admin.demo@mota-sih.gov.in` | Scheme catalogue, version locking, operational analytics |

---

## 4. 39-Step End-to-End Demonstration Sequence

### Phase A: Applicant Workflow (Steps 1–18)
1. **Navigate to Portal**: Open `http://localhost:3000`. Show official MoTA branding, tribal art accents, and bilingual accessibility header.
2. **Citizen Registration / Login**: Login as the demo applicant.
3. **Scheme Discovery**: Open Schemes page (`/schemes`). View the 5 official MoTA schemes:
   - Pre-Matric Scholarship for ST Students (Class IX & X)
   - Post-Matric Scholarship for ST Students
   - National Fellowship for Higher Education of ST Students (NFST)
   - National Overseas Scholarship for ST Candidates (NOS)
   - National Scholarship for Higher Education (Top Class)
4. **Inspect Scheme Details**: Click on *National Fellowship (NFST)*.
5. **Review Eligibility Criteria**: Show deterministic criteria (M.Phil / Ph.D enrollment, ST community status, UGC/CSIR qualification).
6. **Scheme Version Confirmation**: Show that the scheme is on published Version `1.0.0` with official MoTA guideline references.
7. **Initiate Application**: Click "Apply Now". An application draft is created with reference `REF-DEMO-NFST-001`.
8. **Dynamic Form Completion**: Fill in educational qualification and demographic details.
9. **Document Upload**: Upload test files clearly marked `DEMO / TEST DOCUMENT`:
   - ST Caste Certificate (PDF)
   - University Admission Letter (PDF)
   - Income Declaration (PDF)
10. **Malware Scanning State**: Show upload state displaying `Clean` (scanned via ClamAV adapter).
11. **Document Intelligence (OCR/AI)**: Trigger assistive document processing.
12. **Assistive Insights Display**: Show extracted fields, OCR preview, and AI classification confidence.
13. **Notice AI Limitation Banner**: Show notice: *"AI-generated information is assistive and requires human/official verification."*
14. **Application Submission**: Review summary and click "Submit Application".
15. **Submission Confirmation**: Show reference number generation and status `SUBMITTED`.
16. **Notification Trigger**: Check Notifications (`/notifications`). Show in-app notice *"Application REF-DEMO-NFST-001 Submitted Successfully"*.
17. **View Application Timeline**: Open application details (`/applications/[id]`). Show chronological audit timeline.
18. **Deficiency Notification Simulation**: Observe scenario where an officer requests document clarification.

### Phase B: Scrutiny Officer Workflow (Steps 19–31)
19. **Officer Login**: Login as Scrutiny Officer (`officer.demo@mota-sih.gov.in`).
20. **Officer Work Queue**: Navigate to `/admin/work-queue`. View unassigned cases sorted by submission date and priority.
21. **Claim / Assign Case**: Assign `REF-DEMO-NFST-001` to current scrutiny officer.
22. **Open Scrutiny View**: Navigate to `/admin/applications/[id]`.
23. **Review Deterministic Eligibility**: View explainable rule evaluation table (all passed criteria with official MoTA source citations).
24. **Examine Uploaded Documents**: Open document viewer.
25. **Review OCR & Extraction**: Inspect extracted university name and admission date alongside original PDF.
26. **Evaluate Consistency Findings**: Review cross-document consistency findings.
27. **Raise Deficiency**: Click "Raise Deficiency" requesting: *"Please re-upload higher resolution ST Caste Certificate"*. Application status moves to `DEFICIENCY`.
28. **Applicant Resubmission & Resolve**: Record applicant clarification and click "Resolve Deficiency".
29. **Add Officer Case Note**: Enter internal note: *"University admission verified with AI-assisted review. Recommend approval."* (Internal only).
30. **Record Officer Administrative Decision**: Move application status to `DOCUMENT_VERIFICATION` / `SCRUTINY`.
31. **Audit Trail Verification**: Verify that every action created an immutable `AuditLog` entry.

### Phase C: Administrator & System Truth Workflow (Steps 32–39)
32. **Admin Login**: Access system as Scheme Administrator (`admin.demo@mota-sih.gov.in`).
33. **Open Operational Analytics**: Navigate to `/admin/applications` and Analytics dashboard.
34. **Database-Derived Operational Metrics**: Review application counts by status, scheme distribution, and document processing volume.
35. **Filter Analytics**: Filter metrics by scheme (`NFST`, `POST_MATRIC`) and date window.
36. **Inspect Officer Workload**: Review assigned case counts across officers.
37. **Government Integrations Status**: Navigate to `/admin/integrations`.
38. **Government Integration Truth Audit**: Show that all 5 adapters truthfully display their status:
    - UIDAI: `REQUIRES AUTHORIZED ACCESS`
    - DigiLocker: `REQUIRES AUTHORIZED ACCESS`
    - NSP: `INTEGRATION DISABLED`
    - DBT: `INTEGRATION DISABLED`
    - MoTA Dashboard: `NOT CONFIGURED / DISABLED`
39. **Demonstrate Truth Boundary**: Emphasize to evaluators that no mock green "Verified" ticks appear for integrations without authorized government credentials.

---

## 5. Safe Demo Reset Mechanism
To restore the platform to a pristine state after an evaluation round:

```bash
# Execute safe demo reset script
python infra/scripts/demo_reset.py

# Optional dry run to inspect records that would be removed:
python infra/scripts/demo_reset.py --dry-run
```

What the Reset Does:
- Deletes only applications with `is_demo = True` or reference prefix `DEMO-`/`REF-DEMO-`.
- Removes demo documents, case notes, timeline events, and test notifications.
- **Never deletes** official seeded schemes, scheme versions, eligibility rules, or system roles.
