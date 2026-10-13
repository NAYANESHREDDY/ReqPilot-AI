# ReqPilot AI — Report Correction and Comprehensive Technical Audit

**Date**: 2026-10-14T00:55:00+05:30  
**Audit Scope**: Comprehensive factual, evidence, code, and academic alignment audit of `ReqPilot_AI_Project_Report.docx` and `ReqPilot_AI_Project_Report.pdf`.  
**Preservation Constraint**: The Title Page / Cover Page layout and Figure 6.1 (Hero UI image on printed Page 27) were **strictly preserved untouched** per prompt instructions.

---

## 1. Baseline Inventory & Cryptographic Hashes

### Baseline Artifacts (Prior to Sprint Changes)
- **Baseline DOCX**: `report_output/ReqPilot_AI_Project_Report.docx.bak_20261014_004613`  
  - File Size: `1,562,815 bytes`  
  - SHA-256: `113f890da975059d3195232759cbec1967054630c207979f2e1fc8592caed486`
- **Baseline PDF**: `report_output/ReqPilot_AI_Project_Report.pdf.bak_20261014_004613`  
  - File Size: `898,662 bytes`  
  - SHA-256: `b117f6e0cbb5dc8dde86c7c2f80b9cbcdcb72bff47bd884d70048df5186bdbaf`

### Corrected Deliverables (Post-Sprint Verification)
- **Corrected DOCX**: `report_output/ReqPilot_AI_Project_Report_Corrected.docx`  
  - File Size: `1,563,812 bytes`  
  - Status: Fully formatted, clean Unicode, table pagination rules applied.
- **Corrected PDF**: `report_output/ReqPilot_AI_Project_Report_Corrected.pdf`  
  - File Size: `363,992 bytes`  
  - Total Pages: **35 rendered A4 pages** ($\ge 25\text{ page}$ requirement met).

---

## 2. Issues Identified, Audited, and Corrected Across Report Pages

| Page / Section | Original Issue Identified | Correction Applied | Verified Repository Evidence |
| :--- | :--- | :--- | :--- |
| **Page 3 (Sec 1.2)** | Grammatical error: *"an production-grade modular workspace"*. | Corrected to *"a production-grade modular workspace"*. | Linguistic audit. |
| **Page 3 (Sec 1.2)** | Unverifiable absolute claim: *"every analytical insight is explainable... and grounded in verifiable source document excerpts"*. | Refined to *"insights are traceable, structurally auditable, and grounded in verifiable source document excerpts where direct textual evidence exists"*. | Distinguishes text extraction from heuristic estimations. |
| **Page 4 (Sec 1.4)** | Generic citation of Standish Group Chaos Report with unverified 60% figure. | Cited empirical literature on project overruns ([1], [7], [9]) and updated reference to *"CHAOS Report 2015: Decision Latency and Project Success"*. | Software engineering literature ([Pressman, Boehm]). |
| **Page 7 (Sec 2.2)** | Unsupported absolute: *"word processors possess zero semantic awareness"*. | Replaced with *"standard word processors lack specialized requirements-engineering semantic validation"*. | Academic tone calibration. |
| **Page 9 (Sec 2.4)** | Promotional claim: *"fundamentally superior architectural approach"*. | Replaced with *"integrated Multi-Agent Cooperative Engineering Fabric"*, focusing on architectural coupling. | Academic neutrality rule. |
| **Page 10 (Sec 2.4)** | Over-promising claim: *"identifies affected artifacts with zero human guesswork"*. | Replaced with *"identifies candidate affected artifacts for human engineering review"*. | Aligns with human-in-the-loop design. |
| **Page 11 (Sec 3.2)** | Ambiguity among 9 features, 10 tabs, and 15 agents. | Reconciled hierarchy: 9 core functional capability domains, 10 interactive frontend workspace tabs, and 15 backend agents across an 8-step pipeline. | [`orchestrator.py`](file:///c:/Users/ch.nayanesh%20reddy/Downloads/ReqPilot_AI_recovered_audited/fsd_pro/backend/app/agents/orchestrator.py) lines 98–140. |
| **Page 12 (Table 3.1)** | Table split across pages without header repetition; rows split across margins. | Added `<w:tblHeader/>` to header row and `<w:cantSplit/>` across all rows. | Word table layout compliance. |
| **Page 13 (Sec 3.4)** | Target latency (250 ms p95, 2.5s analysis) presented without clarifying specification target vs. measured cloud LLM latency. | Clarified as an architectural operational target; documented that measured cloud LLM pipeline runs take 33–46s under API cooldowns. | Official evaluation runner logs (`run_eval.py`). |
| **Page 13 (Sec 3.4)** | Security over-claim: *"Input sanitization shall neutralize prompt injection tokens"*. | Replaced with *"Input sanitization regex-filters known prompt injection phrases... mitigating direct prompt override attempts"*. | [`llm_adapter.py`](file:///c:/Users/ch.nayanesh%20reddy/Downloads/ReqPilot_AI_recovered_audited/fsd_pro/backend/app/agents/llm_adapter.py) line 38 (`sanitize_untrusted_input`). |
| **Page 15 (Table 3.2)** | Smart Campus presented as an active deployed project. | Clarified as an illustrative multi-stakeholder specification test fixture. | [`backend/uploads/`](file:///c:/Users/ch.nayanesh%20reddy/Downloads/ReqPilot_AI_recovered_audited/fsd_pro/backend/uploads/). |
| **Page 16 (Sec 4.1)** | Figure 4.1 caption ambiguity with 5 tiers. | Renamed to *"Figure 4.1 – High-level multi-tier system architecture of the ReqPilot AI platform"*. | Architectural diagram audit. |
| **Page 18 (Table 4.1)** | Endpoint `/api/projects/{id}/change-impact/simulate` wrapped awkwardly across margins; no cantSplit. | Cleanly formatted with line break `/api/projects/{id}/\nchange-impact/simulate`; added tblHeader and cantSplit. | FastAPI route in [`api/change_impact.py`](file:///c:/Users/ch.nayanesh%20reddy/Downloads/ReqPilot_AI_recovered_audited/fsd_pro/backend/app/api/change_impact.py). |
| **Page 19 (Table 4.2)** | Table 4.2 listed only 7 entities while text claimed 23 tables. | Renamed Table 4.2 to *"Selected core database entity specifications"*; added complete inventory of all 23 SQLAlchemy tables to the preceding text. | Verified via `Base.metadata.tables.keys()` in [`backend/app/models.py`](file:///c:/Users/ch.nayanesh%20reddy/Downloads/ReqPilot_AI_recovered_audited/fsd_pro/backend/app/models.py). |
| **Page 20 (Sec 4.4)** | Figure 4.3 presented as complete ER diagram. | Labeled as *"Figure 4.3 – Conceptual Entity-Relationship (ER) diagram of core ReqPilot AI database entities"*. | ER scope clarification. |
| **Page 21 (Sec 5.1)** | Redundant phrasing: *"modern, robust, modern open-source technologies"*. | Corrected to *"robust open-source technologies"*. | Stylistic cleanup. |
| **Page 24 (Listing 5.2)** | Cyclic dependency fallback portrayed as an ordinary valid schedule. | Labeled as *"Listing 5.2 – NetworkX DAG Task Scheduling with Fallback Handling (scheduling_agent.py excerpt)"*; added comments clarifying cyclic fallback. | [`scheduling_agent.py`](file:///c:/Users/ch.nayanesh%20reddy/Downloads/ReqPilot_AI_recovered_audited/fsd_pro/backend/app/agents/scheduling_agent.py) lines 35–48. |
| **Page 25 (Listing 5.3)** | Listing 5.3 showed outdated mock arguments that did not match the actual `ChangeImpactAgent.analyze_change` signature. | Updated code listing to match actual parameters: `target_req_id`, `new_summary`, `new_description`, `all_requirements`, `all_modules`, `all_tasks`, `all_tests`. Clarified heuristic risk/delay assessment. | [`change_impact_agent.py`](file:///c:/Users/ch.nayanesh%20reddy/Downloads/ReqPilot_AI_recovered_audited/fsd_pro/backend/app/agents/change_impact_agent.py) lines 25–150. |
| **Page 27 (Sec 6.3)** | Unclear test scope and execution date. | Documented pytest 8.3 execution across 46 unit and regression tests on 2026-10-14 (10.09s, 100% pass rate). | `python -m pytest backend/tests -q`. |
| **Page 28 (Table 6.2)** | Macro-F1 aggregation methodology not explicitly disclosed. | Disclosed that aggregate macro-F1 (0.8710) is the unweighted arithmetic mean of individual domain macro-F1 scores, treating each domain equally. | Scorer arithmetic in [`scorer.py`](file:///c:/Users/ch.nayanesh%20reddy/Downloads/ReqPilot_AI_recovered_audited/fsd_pro/evaluation/multi_project/scripts/scorer.py). |
| **Page 29 (Sec 6.5)** | Risk of dismissing all benchmark misclassifications as annotation flaws. | Delineated the 8 misclassifications: explained that Banking Management errors (`LOAN MANAGEMENT`, `DEBIT CARD MANAGEMENT`) stem from model synthesizing specific domain modules penalized by rigid gold references, whereas E-Commerce and Library involved boundary routing. | Error analysis audit. |
| **Page 30 (Sec 6.7)** | Over-claiming universal generalization from synthetic drone test. | Explicitly stated that synthetic drone discovery is a functional proof-of-concept for dynamic pipeline preservation, not proof of universal accuracy on all arbitrary unseen domains. | Sprint 2 verification evidence. |

---

## 3. Verified Four-Domain Evaluation Benchmark Snapshot

All metrics reported in Table 6.2, Figure 6.2, Chapter 6, Chapter 7, and the Abstract were verified against the latest completed evaluation run artifacts:

| Project Domain | Verified Run ID | Gold Reference SHA-256 | Matched Denominator | Correct Predictions | Matched Accuracy | Penalized Accuracy | Macro-F1 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **EV Charging** | `9d9a6a23` | `de7b0f66dc9ffec90cc...ef19` | 58 | 56 | **96.55%** | 96.55% | 0.9741 |
| **E-Commerce** | `a0a716cb` | `9096b24889b6f213e45...8d0` | 36 | 35 | **97.22%** | 94.59% | 0.9677 |
| **Library Management** | `221074ed` | `158664146dd1936731d...a950` | 24 | 23 | **95.83%** | 92.00% | 0.9604 |
| **Banking Management** | `1616700d` | `50916a000e2f6f83829...9af8` | 25 | 21 | **84.00%** | 84.00% | 0.5818 |
| **Combined 4-Domain Suite** | Official Runs | **Unchanged Frozen References** | **143** | **135** | **94.41%** | **92.47%** | **0.8710** |

- **Official Scorer Hash**: `b6c599655cc7c8e8fe8550c8e74c2bd13335ff6ec41f859a0354b3932a3655fb` (**Verified Unaltered**).
- **Hospital Management Exclusion**: Documented in Section 6.6 as excluded from active evaluation and archived under `evaluation/multi_project/archived/hospital_management/` due to confirmed annotation defects (48+ ambiguous labels in original gold reference).

---

## 4. Test Suite and Build Verification

- **Automated Test Command**: `python -m pytest backend/tests -q --tb=short`
- **Observed Result**: **46 passed**, 16 Pydantic deprecation warnings in 10.92s (100% test pass rate).
- **Backend Import Verification**: `from backend.app.main import app` passed cleanly with 0 errors.
- **Frontend Build Verification**: `npm run build` completed in 2.44s with 0 errors.
- **Title Page & Figure 6.1**: Verified completely untouched and intact.
