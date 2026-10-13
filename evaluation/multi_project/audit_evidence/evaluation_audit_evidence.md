# Independent Audit & Evidence Report: ReqPilot AI Evaluation Pipeline

**Auditor / Investigator**: Senior AI Evaluation Engineer & Software Research Auditor  
**Date**: October 13, 2026  
**Target Repository**: `C:\Users\ch.nayanesh reddy\Downloads\ReqPilot_AI_recovered_audited\fsd_pro`  
**Evaluation Target**: `evaluation/multi_project/`  
**Scope**: Verification of matching algorithms, reference provenance, LLM execution status, and the 100% EV accuracy claim.

---

## Section A: Environment and File Inventory

### 1. Execution Environment
- **Operating System**: Windows 11 (Windows-10-10.0.26200-SP0)
- **Python Version**: Python 3.11.9 (tags/v3.11.9:de54cf5, MSC v.1938 64 bit AMD64)
- **Primary Database**: `backend/reqpilot.db` (Preserved intact, SHA-256: `abc1e7028050e60139969f5dae0633a8851b377cdc841d6180ef7b1a9be566cd`)
- **Working Directory**: `C:\Users\ch.nayanesh reddy\Downloads\ReqPilot_AI_recovered_audited\fsd_pro`

### 2. Complete File Inventory & Cryptographic Hashes
A dedicated inventory file has been generated at:
`evaluation/multi_project/audit_evidence/file_inventory_sha256.csv`

Key artifact summary:
| Component | File Path | Size (Bytes) | SHA-256 Checksum |
|---|---|---|---|
| Scorer Engine | `evaluation/multi_project/scripts/scorer.py` | 8,021 | `d031e67b2ff63ce0e7cf239cb328f268b8132ca5828a2a5146c310b9dbcb111e` |
| Scorer Test Suite | `evaluation/multi_project/scripts/test_scorer_robustness.py` | 2,752 | `10046b0bfbbbebb12c823055964d42ec2e022f4625b5a1cf6a5df578c772cb6d` |
| Report Generator | `evaluation/multi_project/scripts/generate_reports.py` | 5,564 | `3ecf039129e924a4f895c1a7924443905cb33a6f15dd649df18c39e25d2dbf11` |
| Manifest | `evaluation/multi_project/manifest.json` | 2,873 | `b537dcf51421c43f721d120a1eb1d746369528d70b7724128f7895e6347c617a` |
| EV Gold Reference | `evaluation/multi_project/benchmark/ev_charging/gold_reference.json` | 17,994 | `96a7516a50fe86e8810058bfe0dc8ca3e372551cf167576f30a990ec86c05d76` |
| EV Run Output | `evaluation/multi_project/runs/ev_charging_run_1c57d2e2/pipeline_output.json` | 95,835 | `95a37130dd5112f205f429fa900a359db5a12260ad08ff81ef80a563bc18408f` |
| Summary CSV | `evaluation/multi_project/results/summary.csv` | 788 | `66870020302824cf4d6bb0bb92d77054f7aeb9e4f51fae13454b5dfd97cecebb` |

---

## Section B: Matching Algorithm Audit

### Code Trace of `match_prediction_to_gold()` (`scripts/scorer.py:46-77`)

```python
def match_prediction_to_gold(pred_req, gold_details):
    pred_texts = [
        normalize_text(pred_req.get('source_excerpt')),
        normalize_text(pred_req.get('description')),
        normalize_text(pred_req.get('summary'))
    ]
    pred_texts = [t for t in pred_texts if t]
    
    candidates = []
    for gid, ginfo in gold_details.items():
        gold_texts = [
            normalize_text(ginfo.get('statement')),
            normalize_text(ginfo.get('summary'))
        ]
        gold_texts = [t for t in gold_texts if t]
        
        matched = False
        for pt in pred_texts:
            for gt in gold_texts:
                if len(pt) >= 15 and len(gt) >= 15:
                    if pt in gt or gt in pt:
                        matched = True
                        break
            if matched:
                break
                
        if matched:
            candidates.append(gid)
            
    if len(candidates) == 1:
        return candidates[0], 'UNIQUE_MATCH'
    elif len(candidates) > 1:
        return None, 'AMBIGUOUS_MATCH'
    else:
        return None, 'UNMATCHED'
```

### Detailed Answers to Audit Questions:
1. **Basis of Matching**: Matching is strictly based on **normalized text substring containment** between predicted fields (`source_excerpt`, `description`, `summary`) and gold fields (`statement`, `summary`). Positional indexing and string ID matching have been **completely eliminated**.
2. **Short Prediction Multiple Matching**: If a short prediction matches multiple gold requirements, `len(candidates) > 1`, and it immediately returns `(None, 'AMBIGUOUS_MATCH')`.
3. **Ambiguous Matches Excluded**: Yes. Ambiguous matches return `None` as the gold ID and are excluded from the `matched_pairs` accuracy denominator.
4. **Duplicate Prevention**: In `score_run` (`scorer.py:108-112`), `assigned_gold_ids` tracks claimed gold IDs. If a second prediction maps to an already-assigned gold ID, it is recorded in `duplicate_gold_matches` and rejected from `matched_pairs`.
5. **One-to-One Guarantee**: Yes. The combination of candidate uniqueness check and `assigned_gold_ids` enforcement guarantees strictly injective (one-to-one) matching.
6. **Accounting of Unmatched Entries**:
   - `unmatched_predictions` is recorded.
   - `unmatched_gold_entries` is computed as `[gid for gid in gold_details if gid not in assigned_gold_ids]`.
7. **Risk of Generic Phrases**: A safety filter `len(pt) >= 15 and len(gt) >= 15` prevents trivially short matches. However, if two distinct gold requirements share a long generic boilerplate phrase (>15 characters), a prediction containing that boilerplate will detect both candidates and correctly fall back to `AMBIGUOUS_MATCH`.
8. **Determinism**: The algorithm is 100% deterministic (no stochastic search, embeddings, or random seeds).
9. **Denominator Formulation**: The reported semantic classification accuracy denominator is **`valid_matched_denominator`** (`len(matched_pairs)`).
10. **Penalization Status**: Currently, `classification_evaluation.accuracy` measures **precision on validly matched requirements**. It does **not** penalize for omitted gold requirements or unmatched predictions in that specific metric; however, matching coverage and unmatched counts are reported separately.

---

## Section C: Verification of the 100% EV Result

All 58 predicted requirements in `ev_charging_run_1c57d2e2` and all 58 gold entries in `benchmark/ev_charging/gold_reference.json` were audited row-by-row.

The full 58-row evidence audit is saved at:
`evaluation/multi_project/audit_evidence/ev_charging_match_audit.csv`

### Audit Findings on EV 100% Accuracy:
1. **Why It Scores 100% (58/58)**:
   - In `ev_charging`, the 58 statements in the input specification were all successfully ingested and extracted.
   - Because `ExtractionAgent` grounds each requirement with its exact `source_excerpt` from the uploaded document, every predicted requirement carries its verbatim specification sentence.
   - The gold reference statements in `gold_reference.json` were derived from the exact same specification text.
   - Therefore, content matching achieves a **1-to-1 bijective mapping for all 58 requirements** with zero false matches and zero duplicates.
   - In all 58 cases, the predicted module (`Charging Station Management`, `Booking & Scheduling`, `Notification Service`, etc.) matches the canonical module established in the independent oracle.
2. **Reverse Direction Check**:
   - Every single one of the 58 gold requirements is matched by exactly one unique prediction. There are 0 orphan gold requirements.
3. **Conclusion on EV Result**: The 100% accuracy on matched pairs is **substantiated** under the definition of agreement with the historical EV specification oracle.

---

## Section D: Ground-Truth Independence and Leakage Audit

| Domain | Source of Gold Reference | Independence Status | Leakage Risk Assessment |
|---|---|---|---|
| `ev_charging` | Independent capability oracle in `validate_ev_independent.py` created before multi-project harness | **VERIFIED** | Source statements come from the original specification. Module labels were established prior to the multi-project run. No predictions were used to modify expected labels. |
| `hospital_management` | Historical database records from pre-existing project `af3386c4-4e35...` | **PARTIALLY VERIFIED** | The 124 requirements and 11 modules were derived from historical runs. 27 requirements not matching generic enterprise patterns are labeled `UNASSIGNED_OR_NULL`. Provenance is internally derived rather than external consensus. |
| `ecommerce_platform` | Authored IEEE 830 specification & domain capability mapping | **VERIFIED** | Authored independently prior to the evaluation runs. Module expectations reflect standard e-commerce architecture. |
| `banking_management` | Authored core banking specification & domain capability mapping | **VERIFIED** | Authored independently prior to the evaluation runs. Module expectations reflect standard banking architecture. |
| `library_management` | Authored ILS specification & domain capability mapping | **VERIFIED** | Authored independently prior to the evaluation runs. Module expectations reflect standard library system architecture. |

---

## Section E: Independent Metrics Recalculation

All metrics were recalculated directly from the immutable outputs and frozen references. The comparative table is preserved in:
`evaluation/multi_project/audit_evidence/independent_metrics_recalculation.csv`

### Recalculated Results:
1. **`ev_charging`** (Run `1c57d2e2`):
   - Predicted: 58 | Gold: 58 | Matched: 58 | Unmatched: 0
   - Matched-Pair Accuracy: **100.0%** | Macro F1: **1.0000** | Penalized End-to-End Accuracy: **100.0%**
2. **`hospital_management`** (Run `4046c3ca`):
   - Predicted: 124 | Gold: 124 | Matched: 124 | Unmatched: 0
   - Matched-Pair Accuracy: **78.23%** (97/124) | Macro F1: **0.9167** | Penalized End-to-End Accuracy: **78.23%**
3. **`ecommerce_platform`** (Run `1e2d6f1a`):
   - Predicted: 37 | Gold: 36 | Matched: 36 | Unmatched Preds: 1 | Unmatched Gold: 0
   - Matched-Pair Accuracy: **44.44%** (16/36) | Macro F1: **0.3356** | Penalized End-to-End Accuracy: **43.24%** (16/37)
4. **`banking_management`** (Run `ba26cb8e`):
   - Predicted: 25 | Gold: 25 | Matched: 25 | Unmatched: 0
   - Matched-Pair Accuracy: **36.00%** (9/25) | Macro F1: **0.3979** | Penalized End-to-End Accuracy: **36.00%**
5. **`library_management`** (Run `037fa230`):
   - Predicted: 24 | Gold: 24 | Matched: 24 | Unmatched: 0
   - Matched-Pair Accuracy: **66.67%** (16/24) | Macro F1: **0.6679** | Penalized End-to-End Accuracy: **66.67%**

---

## Section F: LLM Execution and Fallback Audit

| Project | Run ID | Configured Provider / Model | LLM Attempted | LLM Succeeded | Fallback Used | Evidence / Failure Reason |
|---|---|---|---|---|---|---|
| `ev_charging` | `1c57d2e2` | `groq` / `openai/gpt-oss-120b` | True | **True** (8 AI reqs) | False | Valid evidence of live LLM enrichment |
| `hospital_management` | `4046c3ca` | `groq` / `openai/gpt-oss-120b` | True | **False** (0 AI reqs) | **True** | Groq HTTP 429 (`rate_limit_exceeded`, TPM limit 8,000) |
| `ecommerce_platform` | `1e2d6f1a` | `groq` / `openai/gpt-oss-120b` | True | **False** (0 AI reqs) | **True** | Groq HTTP 429 (`rate_limit_exceeded`, TPM limit 8,000) |
| `banking_management` | `ba26cb8e` | `groq` / `openai/gpt-oss-120b` | True | **True** (8 AI reqs) | False | Valid evidence of live LLM enrichment |
| `library_management` | `037fa230` | `groq` / `openai/gpt-oss-120b` | True | **False** (0 AI reqs) | **True** | Groq HTTP 429 (`rate_limit_exceeded`, TPM limit 8,000) |

---

## Section G: Scorer Testing & Adversarial Validation

Two complete test suites were executed:
1. **Baseline Robustness Test** (`scripts/test_scorer_robustness.py`): 3/3 passed.
2. **Adversarial Test Suite** (`audit_evidence/test_adversarial_scorer.py`): 10/10 passed.

Complete terminal log captured in:
`evaluation/multi_project/audit_evidence/test_execution_log.txt`

---

## Section H: Final Assessment & Ranked Severity

### 1. Status of Reported Claims:
- **EV 100% Accuracy**: `VERIFIED` on valid matched pairs against the specification-derived oracle.
- **Cross-Domain LLM Claims**: `PARTIALLY VERIFIED`. Only EV and Banking reflect actual LLM extraction; the other three reflect deterministic fallback output due to Groq free-tier rate limits.
- **Scorer Reliability**: `VERIFIED`. The updated content-grounded matcher is deterministic, injective, and robust against adversarial reordering and renumbering.

### 2. Issues Ranked by Severity:
- **High Severity**: Three projects (`hospital_management`, `ecommerce_platform`, `library_management`) used deterministic fallback due to Groq 429 rate limits.
- **Medium Severity**: In `ecommerce_platform`, 1 extra requirement was extracted (37 predicted vs. 36 gold). Reporting matched-pair accuracy (44.44%) without reporting penalized end-to-end accuracy (43.24%) slightly overstates coverage.
- **Low Severity**: Hospital gold reference contains 27 `UNASSIGNED_OR_NULL` targets due to specialized clinical requirements not mapping to generic enterprise capabilities.

### 3. Minimum Safe Next Steps:
1. Implement a multi-key rotational fallback harness utilizing the user's 22 active Gemini API keys (`gemini-1.5-flash`) so that Hospital, E-Commerce, and Library can achieve 100% true LLM extraction runs without HTTP 429 errors.
2. Report both **Matched-Pair Accuracy** and **Penalized End-to-End Accuracy** in all summary tables.
