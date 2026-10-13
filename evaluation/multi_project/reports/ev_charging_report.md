# Evaluation Report: EV Charging Station Management System (ev_charging)

## Run Information
- **Run ID**: 1c57d2e2-509c-48d3-848c-1fd3453a0e48
- **Timestamp**: 2026-10-12T17:14:12.517675
- **Provider / Model**: groq / openai/gpt-oss-120b
- **LLM Extraction Succeeded**: True
- **Deterministic Fallback Used**: False

## Content-Grounded Requirement Matching
- **Predicted Requirements**: 58
- **Reference Requirements**: 58
- **Uniquely Matched Pairs**: 58
- **Unmatched Predictions**: 0
- **Ambiguous Predictions**: 0
- **Duplicate Gold Matches**: 0
- **Unmatched Reference Entries**: 0

## Semantic Classification Metrics (On Matched Requirements)
- **Matched Denominator**: 58
- **Correct Classifications**: 58
- **Accuracy**: 100.0%
- **Macro Precision**: 1.0
- **Macro Recall**: 1.0
- **Macro F1**: 1.0

### Per-Module Breakdown
| Module | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| AUTHENTICATION | 4 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| BOOKING | 9 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| CHARGING-SESSION | 5 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| CHARGING-STATION | 11 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| DATA | 7 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| GATEWAY | 1 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| MAINTENANCE | 5 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| NOTIFICATION | 7 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| PAYMENT | 4 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| REPORTING | 5 | 0 | 0 | 1.0 | 1.0 | 1.0 |

### Classification Errors (0 total)

## Structural Integrity Checks
- **Total Requirements**: 58
- **Requirements with Assigned Tasks**: 58 (100.0%)
- **Total Modules**: 11
- **Total Architecture Relations**: 23
- **Total Test Cases**: 58
- **Untested Requirements**: 0

## Declared Non-Evaluated Metrics
- semantic_test_step_oracle: NOT EVALUATED (No independent ground-truth test assertions)
- code_level_traceability_oracle: NOT EVALUATED (No source code repository under analysis)
- dynamic_runtime_latency_oracle: NOT EVALUATED (Pipeline runs offline)
