# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# Scheme Policy Governance & Rule Change Protocol

> **Classification:** Statutory Scheme Administration Protocol  
> **Status:** APPROVED OPERATIONAL SPECIFICATION (Phase 15)  
> **Core Mandate:** Official Source Traceability, Deterministic Integrity, Zero-AI Modification

---

## 1. Absolute Scheme Governance Rules

1. **NO AUTOMATED AI SCHEME MODIFICATION:** Under no circumstances shall an AI model, LLM, or automated script directly modify, create, or publish scholarship eligibility rules or scheme criteria.
2. **OFFICIAL SOURCE TRACEABILITY:** Every scholarship rule must cite an authentic official government source:
   - Official Ministry notification or gazette reference.
   - Exact publication date and official URL (e.g. `tribal.nic.in/ScholarshiP.aspx`).
   - Page and section number of statutory guidelines.
3. **VERSION IMMUTABILITY:** Once a scheme version is set to `is_active = true` and applicants submit applications against it, its rules and criteria are **frozen forever**. Policy changes require drafting and publishing a new sequential scheme version (`version_number = N + 1`).
4. **HISTORICAL APPLICATION INTEGRITY:** Existing submitted applications permanently retain their original scheme version ID. Re-evaluating or auditing historical applications always executes against the exact rules in effect on their submission date.

---

## 2. Scheme Change Lifecycle Protocol

```text
┌──────────────────────────────────────┐
│ 1. OFFICIAL POLICY NOTIFICATION      │ Official MoTA Gazette / Guideline Published
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 2. SOURCE VERIFICATION & EXTRACTION  │ Nodal Officer verifies URL, Section, Effective Date
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 3. DRAFT VERSION CREATION            │ Scheme Admin creates new version in DRAFT state
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 4. DETERMINISTIC RULE CODIFICATION   │ Update Python rule criteria (income, age, marks)
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 5. REGRESSION & BOUNDARY TESTING     │ Run automated test suite against sample test cases
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 6. DUAL HUMAN APPROVAL               │ Scheme Admin + Directorate Sign-off
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│ 7. PUBLISH & ARCHIVE PREVIOUS        │ Set new version active; archive old version
└──────────────────────────────────────┘
```

---

## 3. Official MoTA Schemes Covered

| Scheme Code | Scheme Title | Current Baseline Version | Statutory Income Threshold |
| :--- | :--- | :--- | :--- |
| **`NFST`** | National Fellowship for Higher Education of ST Students | Version 1.0 (Active) | No ceiling (Merit-based M.Phil / Ph.D.) |
| **`TOPCLASS`**| National Scholarship for Higher Education (Top Class) | Version 1.0 (Active) | ≤ Rs. 6,00,000 per annum |
| **`NOS`** | National Overseas Scholarship for ST Candidates | Version 1.0 (Active) | ≤ Rs. 8,00,000 per annum |
