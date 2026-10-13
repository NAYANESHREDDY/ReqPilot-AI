# Multi-Project Ground-Truth Evaluation Report for ReqPilot AI

**Author**: ReqPilot Evaluation Harness & Research Auditor  
**Date**: October 13, 2026  
**Status**: Completed Cross-Domain Audit & Evaluation (Version 3.0 Engine)  
**Evaluated Pipeline**: ReqPilot AI Multi-Agent Architecture (`WorkflowOrchestrator`)  

### Cryptographic Baseline Verification
- **Scorer Script SHA-256**: `b6c599655cc7c8e8fe8550c8e74c2bd13335ff6ec41f859a0354b3932a3655fb` (`evaluation/multi_project/scripts/scorer.py` — Version 3.0)
- **Manifest SHA-256**: `250f981648f991e0b324f23d81a24739655be41e554bba1ea4a9afdcb4c1113c` (`evaluation/multi_project/manifest.json`)
- **EV Gold Reference SHA-256**: `de7b0f66dc9ffec90cc36e8ca132eca7ba275d6bf8e501403f4b056e8c52ef19` (`benchmark/ev_charging/gold_reference.json`)
- **EV Provenance SHA-256**: `46ab09cb35fb2c2c04f310961ca1fb4fabd00c7a5b9fde4aeba9912311de9219` (`benchmark/ev_charging/PROVENANCE.md`)
- **Active Database SHA-256**: `abc1e7028050e60139969f5dae0633a8851b377cdc841d6180ef7b1a9be566cd` (`backend/reqpilot.db` — Verified Untouched During Session)

### Evaluated Pipeline Run Output Hashes
- **EV Charging Run Output**: `411f6857c5920acff69152b5d71cf5e5d062a2e8266a34d2f8d6feddc3680eb4` (`runs/ev_charging_run_1c57d2e2/pipeline_output.json`)
- **Hospital Run Output**: `115853c60974f0ba0d4a75d50e19459e7481395b046eb05d5162d5c4f73d006b` (`runs/hospital_management_run_4046c3ca/pipeline_output.json`)
- **E-Commerce Run Output**: `72b51f4830ae8490a695b3619c093f58bd5b35d3bb4d6537fcc54f05b19f53ad` (`runs/ecommerce_platform_run_1e2d6f1a/pipeline_output.json`)
- **Banking Run Output**: `cb4b315a412b8056c58b4f25be959b33ab9a09876888dbbdc31fa97d29e33c97` (`runs/banking_management_run_ba26cb8e/pipeline_output.json`)
- **Library Run Output**: `1fde2d154ecd3de74141124603e3f3173e5ec77d8c1ff3d9824c67173abbaad7` (`runs/library_management_run_037fa230/pipeline_output.json`)

---

## 1. Executive Summary

This evaluation establishes a reproducible, multi-project benchmark measuring how accurately ReqPilot AI agrees with independently established domain ground-truth references across five distinct software requirements domains:
1. **EV Charging Station Management System** (CleanTech / Smart Transportation)
2. **Hospital Management System** (Healthcare / Clinical Operations)
3. **E-Commerce Platform** (Retail / Multi-vendor Marketplace)
4. **Banking Management System** (FinTech / Core Banking)
5. **Library Management System** (Education / Information Science)

### Key Findings
1. **Pipeline Execution & LLM Status**:
   - **EV Charging Station Management System**: Genuine LLM execution (Groq / `openai/gpt-oss-120b`). LLM extraction succeeded and enriched requirements (`FR-001` through `FR-008`).
   - **Banking Management System**: Genuine LLM execution (Groq / `openai/gpt-oss-120b`). LLM extraction succeeded and enriched requirements (`FR-001` through `FR-008`).
   - **Hospital Management, E-Commerce, Library Management**: LLM requested, but Groq free/on-demand tier Token-Per-Minute (TPM) quota limits (HTTP 429) engaged ReqPilot's built-in deterministic fallback engine. These runs are recorded and audited as **Fallback (HTTP 429)**.
2. **Text Alignment vs. Semantic Classification Correctness**:
   - **Text Alignment**: Measures whether the pipeline extracted the verbatim source requirement statements from the specification without textual distortion or hallucination. In EV Charging, 58 of 58 requirements align exactly (`EXACT_MATCH`).
   - **Semantic Classification**: Measures whether the architectural capability module assigned by ReqPilot's downstream agents agrees with the independently frozen domain taxonomy. High text alignment does not guarantee high semantic accuracy (e.g. Banking has 100% text alignment but only 36.00% semantic classification accuracy).
3. **Database Integrity**:
   - `backend/reqpilot.db` checksum verified identical before and after all runs (`abc1e7028050e601...`). *Audit qualification: No external pre-audit cryptographic commit or notary hash existed prior to this evaluation; therefore, historical status before the audit session cannot be established from the current hash alone.*

---

## 2. Cross-Project Summary Metrics

The metrics below reflect the audited, globally consistent, order-invariant requirement matching (Scorer Version 3.0). To ensure scientific rigor, both **Matched-Pair Accuracy** (evaluated strictly over uniquely matched source requirements) and **Penalized End-to-End Accuracy** ($\frac{\text{Correct}}{\max(\text{Pred}, \text{Gold})}$, where unmatched predictions or missing reference entries count as errors) are reported.

| Domain | Project Title | Run ID | Execution Mode | Pred Reqs | Gold Reqs | Matched Pairs | Matching Coverage | Correct | Matched-Pair Acc | Penalized E2E Acc | Macro Prec | Macro Rec | Macro F1 | Task Coverage | Modules | Relations |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ev_charging` | EV Charging Station Management System | `1c57d2e2` | **Real LLM Run** (Groq) | 58 | 58 | 58 | 100.0% | 58 | **100.0%** | **100.0%** | 1.0000 | 1.0000 | **1.0000** | 100.0% | 11 | 23 |
| `hospital_management` | Hospital Management System | `4046c3ca` | **Fallback** (HTTP 429) | 124 | 124 | 124 | 100.0% | 97 | **78.23%** | **78.23%** | 0.9167 | 0.9167 | **0.9167** | 100.0% | 11 | 21 |
| `ecommerce_platform` | E-Commerce Platform | `1e2d6f1a` | **Fallback** (HTTP 429) | 37 | 36 | 36 | 100.0% | 16 | **44.44%** | **43.24%** | 0.3762 | 0.3194 | **0.3356** | 100.0% | 11 | 23 |
| `banking_management` | Banking Management System | `ba26cb8e` | **Real LLM Run** (Groq) | 25 | 25 | 25 | 100.0% | 9 | **36.00%** | **36.00%** | 0.5000 | 0.3583 | **0.3979** | 100.0% | 8 | 15 |
| `library_management` | Library Management System | `037fa230` | **Fallback** (HTTP 429) | 24 | 24 | 24 | 100.0% | 16 | **66.67%** | **66.67%** | 0.7778 | 0.6151 | **0.6679** | 100.0% | 10 | 21 |

---

## 3. Detailed Project Analysis

### 3.1 EV Charging Station Management System (`ev_charging`)
- **Status**: Genuine LLM-Enabled Run (`groq` / `openai/gpt-oss-120b`).
- **Matching Results**: 58 predicted requirements, 58 reference requirements, 58 uniquely matched pairs (100.0% coverage). All 58 matches are verified as `EXACT_MATCH`.
- **Accuracy**: 100.0% (58/58 correct vs frozen reference). Macro F1: 1.0000.
- **Resolution of Historical 18.97% Anomaly**:
  - In earlier intermediate reports, an ungrounded positional/index-fallback scorer compared requirements using synthetic sequential IDs (`FR-001`, `FR-002`, ...). Because the LLM extraction ordered statements in direct narrative order (promoting search requirements before reservation requirements), an ID phase shift occurred, causing 47 false mismatches.
  - Under content-grounded anchor matching (which identifies requirements by exact/normalized statement text and source anchors), all 58 requirements align 1-to-1 with their true counterparts, verifying 100.0% classification agreement with the established domain architecture.

### 3.2 Hospital Management System (`hospital_management`)
- **Status**: LLM Rate-Limited (HTTP 429) -> Deterministic Engine Fallback.
- **Matching Results**: 124 predicted, 124 reference, 124 uniquely matched pairs (100.0% coverage).
- **Accuracy**: 78.23% (97/124 correct vs frozen reference). Macro F1: 0.9167.
- **Analysis**: High agreement on administrative, patient record, and appointment scheduling modules. The 27 classification errors correspond to specialized clinical domains (Laboratory Information Systems, Pharmacy Dispensation) where generic enterprise heuristics default to `UNASSIGNED_OR_NULL` due to the absence of clinical-specific classifier keywords.

### 3.3 E-Commerce Platform (`ecommerce_platform`)
- **Status**: LLM Rate-Limited (HTTP 429) -> Deterministic Engine Fallback.
- **Matching Results**: 37 predicted, 36 reference, 36 uniquely matched pairs (1 unmatched prediction: `FR-037`).
- **Accuracy**: Matched-Pair Accuracy: 44.44% (16/36). Penalized End-to-End Accuracy: 43.24% (16/37). Macro F1: 0.3356.
- **Analysis**: The pipeline accurately categorized `PAYMENT` (checkout, gateway) and `AUTHENTICATION` (customer login, RBAC). Mismatches occurred in cart management, inventory holds, and catalog browsing, which were assigned to generic `DATA` modules rather than transactional order/reservation modules.

### 3.4 Banking Management System (`banking_management`)
- **Status**: Genuine LLM-Enabled Run (`groq` / `openai/gpt-oss-120b`).
- **Matching Results**: 25 predicted, 25 reference, 25 uniquely matched pairs (100.0% coverage).
- **Accuracy**: 36.00% (9/25 correct vs frozen reference). Macro F1: 0.3979.
- **Analysis**: High precision on `PAYMENT` (fund transfers, NEFT/RTGS, bill payments) and `NOTIFICATION` (transaction alerts). Misses occurred where financial audit logs, KYC compliance, and account lifecycle operations were classified under generic data stores rather than specialized compliance or ledger modules.

### 3.5 Library Management System (`library_management`)
- **Status**: LLM Rate-Limited (HTTP 429) -> Deterministic Engine Fallback.
- **Matching Results**: 24 predicted, 24 reference, 24 uniquely matched pairs (100.0% coverage).
- **Accuracy**: 66.67% (16/24 correct vs frozen reference). Macro F1: 0.6679.
- **Analysis**: Strong alignment on catalog search (`SEARCH`), patron accounts (`AUTHENTICATION`), and overdue fines (`PAYMENT`). Circulation operations (holds, book checkout, loan renewals) were split between booking sessions and storage modules.

---

## 4. Declared Non-Evaluated Metrics & Limitations

1. **Semantic Test Step Execution**: NOT EVALUATED. ReqPilot generates test case descriptions and expected results, but does not execute live automated test runners against running application code.
2. **Code-Level Traceability Integrity**: NOT EVALUATED. Requirements trace to architecture modules, tasks, and test cases, but not to concrete code AST repositories.
3. **Specification Universality**: References are specification-derived benchmarks representing defensible architectural decompositions; they do not represent absolute or single-truth ontologies.
4. **API Quota Constraints**: Groq free/on-demand tier imposes an 8,000 TPM limit on large models (`openai/gpt-oss-120b`), causing burst batch requests to trigger HTTP 429 and engage ReqPilot's built-in fallback engine on 3 of the 5 projects.

---

## 5. Audit Deliverables & Verification Suite

All artifacts are version-controlled and cryptographically frozen under `evaluation/multi_project/`:
- `benchmark/`: Ground-truth references, source specifications, and `PROVENANCE.md` documentation.
- `manifest.json`: Cryptographic SHA-256 hashes verifying reference immutability prior to evaluation.
- `runs/`: Raw immutable pipeline outputs and run metadata.
- `reports/`: Individual project evaluation reports in GitHub Markdown.
- `results/`: `summary.csv`, `summary.json`, `audit_findings.md`, and this `final_report.md`.
- `scripts/`: Scorer (`scorer.py` Version 3.0), report generator (`generate_reports.py`), and test suite (`test_scorer_robustness.py`).
- `audit_evidence/`: Grounded match audits, independent recalculation tables, test suite (`test_adversarial_scorer.py`), and `evaluation_audit_evidence.zip`.
