# Audit Findings: ReqPilot Multi-Project Ground-Truth Evaluation

**Auditor**: Senior AI Evaluation Engineer & Software Research Auditor  
**Date**: October 13, 2026  
**Scope**: Independent audit of `evaluation/multi_project/` artifacts, ground-truth references, pipeline run outputs, and scoring methodology (Scorer Version 3.0).

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

## 1. Project-by-Project Audit Summary Table

The table below records the verified evaluation metrics across all five projects. Both **Matched-Pair Accuracy** (evaluated strictly over uniquely matched source requirements) and **Penalized End-to-End Accuracy** ($\frac{\text{Correct}}{\max(\text{Pred}, \text{Gold})}$, where unmatched predictions or missing reference entries count as errors) are presented.

| Domain | Project Title | Actual Run ID | Execution Mode | Pred Reqs | Gold Reqs | Matched Pairs | Matching Coverage | Correct | Matched-Pair Acc | Penalized E2E Acc | Macro Prec | Macro Rec | Macro F1 | Exact Reference File Used | Exact Run Output File Used |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ev_charging` | EV Charging Station Management System | `1c57d2e2` | **Real LLM Run** (Groq) | 58 | 58 | 58 | 100.0% | 58 | **100.0%** | **100.0%** | 1.0000 | 1.0000 | **1.0000** | `benchmark/ev_charging/gold_reference.json` | `runs/ev_charging_run_1c57d2e2/pipeline_output.json` |
| `hospital_management` | Hospital Management System | `4046c3ca` | **Fallback** (HTTP 429) | 124 | 124 | 124 | 100.0% | 97 | **78.23%** | **78.23%** | 0.9167 | 0.9167 | **0.9167** | `benchmark/hospital_management/gold_reference.json` | `runs/hospital_management_run_4046c3ca/pipeline_output.json` |
| `ecommerce_platform` | E-Commerce Platform | `1e2d6f1a` | **Fallback** (HTTP 429) | 37 | 36 | 36 | 100.0% | 16 | **44.44%** | **43.24%** | 0.3762 | 0.3194 | **0.3356** | `benchmark/ecommerce_platform/gold_reference.json` | `runs/ecommerce_platform_run_1e2d6f1a/pipeline_output.json` |
| `banking_management` | Banking Management System | `ba26cb8e` | **Real LLM Run** (Groq) | 25 | 25 | 25 | 100.0% | 9 | **36.00%** | **36.00%** | 0.5000 | 0.3583 | **0.3979** | `benchmark/banking_management/gold_reference.json` | `runs/banking_management_run_ba26cb8e/pipeline_output.json` |
| `library_management` | Library Management System | `037fa230` | **Fallback** (HTTP 429) | 24 | 24 | 24 | 100.0% | 16 | **66.67%** | **66.67%** | 0.7778 | 0.6151 | **0.6679** | `benchmark/library_management/gold_reference.json` | `runs/library_management_run_037fa230/pipeline_output.json` |

---

## 2. Text Alignment vs. Semantic Classification Correctness

A fundamental methodological distinction is enforced across all reports and audits:
1. **Text Alignment (Extraction Fidelity)**:
   - Evaluates whether ReqPilot's extraction pipeline captured the true requirements statements without hallucination, truncation, or omission.
   - In EV Charging, all 58 requirements matched 100% via `EXACT_MATCH` (`is_exact_or_clean_header_match`).
2. **Semantic Classification (Architectural Mapping Correctness)**:
   - Evaluates whether ReqPilot's downstream agents (`TaskDecompositionAgent`, `ArchitectureAgent`) correctly mapped each requirement to its defensible capability module in the frozen domain reference.
   - Exact text matching does **not** imply 100% semantic accuracy. For instance, Banking Management achieved 100% text alignment (25/25 requirements uniquely matched) but only 36.00% semantic classification accuracy due to heuristic misassignments of compliance and audit requirements.
   - In EV Charging, the 100% semantic score reflects both exact text alignment AND genuine classification agreement across all 58 requirements as verified against the independent oracle.

---

## 3. Scorer Version 3.0 Enhancements & Adversarial Verification

Scorer Version 3.0 resolves the two critical algorithmic weaknesses identified during audit:
1. **Exact-Precedence Allocation (Resolves Greedy Preemption)**:
   - Exact matches (Tier 1) are resolved globally before any partial matches (Tier 2) are considered.
   - An earlier partial substring match cannot steal a gold requirement from a later exact match (`test_regression_01`).
2. **Global Order-Invariance**:
   - Matching is computed over deterministic sets and sorted identifiers.
   - Reversing prediction order produces 100% identical evaluation results (`test_regression_02`).
3. **Context-Embedding Rejection**:
   - Substring containment alone is rejected as proof of semantic equivalence.
   - When a prediction mentions a requirement only in background context (e.g. warning notification mentioning session timeout), it is rejected as insufficient evidence and marked `UNMATCHED` (`test_regression_03`).
4. **Ambiguity and Duplicate Tracking**:
   - Generic phrasing matching multiple gold items is flagged `AMBIGUOUS_MATCH` (`test_regression_04`).
   - Duplicate predictions competing for a single gold item are explicitly flagged in `duplicate_gold_matches` without score inflation (`test_regression_05`).
5. **EV Integrity**:
   - All 58 EV requirements remain verified as 100% exact matches (`test_regression_06`).

### Full Test Suite Results:
- `scripts/test_scorer_robustness.py`: **3 / 3 passed (100% OK)**
- `audit_evidence/test_adversarial_scorer.py`: **16 / 16 passed (100% OK)**
- Total: **19 / 19 tests passing**.

---

## 4. Benchmark Provenance & Limitations

1. **EV Charging**: Derived directly from `validate_ev_independent.py` oracle. Documented in `PROVENANCE.md`.
2. **Hospital Management**: 27 specialized clinical capabilities (Laboratory, Pharmacy) are explicitly modeled as unassigned/null in the reference to prevent false positive credit.
3. **Pre-Audit Database Immutability**: No external pre-audit cryptographic commit or notary hash of `backend/reqpilot.db` existed before the audit session started. Its unchanged status prior to this session cannot be independently established from the current hash alone.
4. **No External Superiority Claims**: References represent defensible domain decompositions, not standardized cross-model benchmarks (e.g. SWE-bench). No claims of superiority over external AI pipelines are claimed.
