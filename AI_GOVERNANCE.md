# Ministry of Tribal Affairs (MoTA) Scholarship & Fellowship Management System
# AI & Automated Decision-Making Governance Policy

> **Classification:** Official Institutional AI Ethics & Governance Framework  
> **Status:** RATIFIED PILOT SPECIFICATION  
> **Core Mandate:** AI is Strictly Assistive; Official Determinations are Deterministic or Human-Decided  
> **Notice:** Specific production cloud model versions are: `OFFICIAL INFORMATION REQUIRED`.

---

## 1. Core Principles of AI Governance

The MoTA Scholarship & Fellowship Management System adheres to the following non-negotiable governance principles:

1. **Deterministic Eligibility:** Scholarship eligibility is evaluated strictly by a rules engine (`RuleEngineService`) executing Python code against published statutory scheme guidelines. **AI never determines eligibility.**
2. **Human-in-the-Loop:** All official decisions (Document Verification, Deficiency Issuance, Award Recommendation, Application Rejection) must be executed by an authenticated human Scrutiny Officer.
3. **Strictly Assistive AI:** AI services (Gemini API, OCR, Vision models) serve exclusively as assistive copilots to help officers spot document anomalies, check image clarity, and extract reference text.
4. **Data Minimization:** No personal identifiers (name, Aadhaar hash, bank account number, mobile number) are forwarded to external AI APIs. Only sanitized document image chunks or anonymized extracted text are submitted.
5. **Fail-Open Operational Continuity:** If the AI service is disabled, throttled, or unreachable, the entire scholarship workflow remains fully functional. Officers verify documents manually without operational disruption.
6. **No Fabricated Output:** Mock and fallback AI modes explicitly return status `ASSISTIVE_MOCK` or `AI_UNAVAILABLE`. The system never fabricates automated "official approvals".

---

## 2. AI Architecture & Integration Boundary

```text
+-------------------------------------------------------------+
|                      FastAPI Backend                        |
|                                                             |
|  +---------------------+        +------------------------+  |
|  | Rule Engine Service |        | Scrutiny Officer Portal|  |
|  | (Deterministic 100%)|        | (Human Decision-Maker) |  |
|  +---------------------+        +------------------------+  |
|            ^                                ^               |
|            |                                | (Advisory)    |
|  +-------------------------------------------------------+  |
|  |                  AIService Abstraction                |  |
|  |                                                       |  |
|  |   [Mode: GEMINI]        [Mode: LOCAL]   [Mode: MOCK]  |  |
|  +-------------------------------------------------------+  |
+-------------------------------------------------------------+
```

---

## 3. Supported AI Engine Configurations

| Engine Mode | Implementation Class | Operational Context | Data Egress Boundary |
| :--- | :--- | :--- | :--- |
| **`GEMINI`** | `GeminiAIService` | Production / Cloud Deployment | Outbound HTTPS to Google AI API. Strictly sanitized document snippets. |
| **`LOCAL`** | `LocalAIService` / Tesseract | Sovereign / Air-gapped Deployment | Zero external network egress. Runs on institutional GPU/CPU servers. |
| **`MOCK`** | `MockAIService` | Development / CI / Demonstration | Local rule-based synthetic extraction. No network egress. |
| **`UNAVAILABLE`**| `UnavailableAIService` | Disaster Recovery / Fallback Mode | Returns standard degraded response. All checks escalate to manual officer review. |

---

## 4. AI Processing Scope & Limitations

### 4.1 Allowed AI Operations
- Document image quality assessment (detecting blur, glare, low resolution, or partial cropping).
- Optical Character Recognition (OCR) of income and caste certificate registration numbers.
- Textual alignment check between applicant-entered annual income and certificate value.
- Summary generation for complex academic fellowship research proposals.

### 4.2 Prohibited AI Operations
- **PROHIBITED:** Automatically rejecting an application based on an AI confidence score.
- **PROHIBITED:** Automatically approving an application or disbursing funds.
- **PROHIBITED:** Evaluating applicant merit, moral character, or fellowship worthiness.
- **PROHIBITED:** Retaining or training models on applicant personal documents.
- **PROHIBITED:** Overriding deterministic scheme eligibility rules.

---

## 5. Confidence Scoring & Escalation Thresholds

When AI extracts data or performs consistency checks, it generates a confidence score between `0.00` and `1.00`:

| Confidence Score | System Behavior | Scrutiny Officer UI Representation |
| :--- | :--- | :--- |
| **≥ 0.85** | High confidence extraction. | Highlighted in green; pre-fills advisory comparison field for officer confirmation. |
| **0.60 – 0.84** | Moderate confidence. | Highlighted in amber; explicitly marked `Requires Officer Verification`. |
| **< 0.60** | Low confidence / Unclear document. | Flagged in red with alert: `AI Extraction Failed - Full Manual Scrutiny Mandatory`. |
| **Service Error** | Fallback mode. | Marked `AI Service Unavailable - Manual Scrutiny Mandatory`. |

---

## 6. Auditability & Explainability

Every invocation of an AI service is recorded in `audit_logs` with:
- Timestamp and calling subsystem.
- Input token hash (not raw PII).
- Returned confidence scores and discrepancy flags.
- Name/version of the executing model engine.
- Officer override actions (recording when an officer disagrees with an AI advisory flag).

*Policy ratified for institutional operations. Model provider versions and sovereign hosting options: `OFFICIAL INFORMATION REQUIRED`.*
