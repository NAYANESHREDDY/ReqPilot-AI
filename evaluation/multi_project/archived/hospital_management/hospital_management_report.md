# Evaluation Report: Hospital Management System (hospital_management)

## Run Information
- **Run ID**: 4046c3ca-29c6-49d7-99f5-242fb68724fe
- **Timestamp**: 2026-10-12T17:15:46.108685
- **Provider / Model**: groq / openai/gpt-oss-120b
- **LLM Extraction Succeeded**: False
- **Deterministic Fallback Used**: True

## Content-Grounded Requirement Matching
- **Predicted Requirements**: 124
- **Reference Requirements**: 124
- **Uniquely Matched Pairs**: 124
- **Unmatched Predictions**: 0
- **Ambiguous Predictions**: 0
- **Duplicate Gold Matches**: 0
- **Unmatched Reference Entries**: 0

## Semantic Classification Metrics (On Matched Requirements)
- **Matched Denominator**: 124
- **Correct Classifications**: 97
- **Accuracy**: 78.23%
- **Macro Precision**: 0.9167
- **Macro Recall**: 0.9167
- **Macro F1**: 0.9167

### Per-Module Breakdown
| Module | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| AUTHENTICATION | 14 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| BOOKING | 18 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| DATA | 22 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| DEPARTMENT | 2 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| FILE | 1 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| GATEWAY | 5 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| NOTIFICATION | 9 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| PAYMENT | 13 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| PROFILE | 1 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| REPORTING | 10 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| SEARCH | 2 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| UNASSIGNED_OR_NULL | 0 | 0 | 27 | 0.0 | 0.0 | 0.0 |

### Classification Errors (27 total)
- **FR-009 -> FR-009** (Patients should be able to view prescriptions issu...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED
- **FR-019 -> FR-019** (Doctors should be able to create electronic prescr...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED
- **FR-020 -> FR-020** (Doctors should be able to modify or cancel prescri...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED
- **FR-021 -> FR-021** (Doctors should be able to request laboratory tests...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED
- **FR-022 -> FR-022** (Doctors should be able to view completed laborator...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED
- **FR-029 -> FR-029** (Laboratory Requirements Laboratory staff should be...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED
- **FR-030 -> FR-030** (Laboratory staff should be able to update the stat...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED
- **FR-033 -> FR-033** (Patients should be able to view their laboratory r...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED
- **FR-035 -> FR-035** (Pharmacy Requirements Pharmacists should be able t...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED
- **FR-037 -> FR-037** (The system should maintain medicine inventory info...): Expected UNASSIGNED_OR_NULL, Predicted UNASSIGNED

## Structural Integrity Checks
- **Total Requirements**: 124
- **Requirements with Assigned Tasks**: 124 (100.0%)
- **Total Modules**: 11
- **Total Architecture Relations**: 21
- **Total Test Cases**: 124
- **Untested Requirements**: 0

## Declared Non-Evaluated Metrics
- semantic_test_step_oracle: NOT EVALUATED (No independent ground-truth test assertions)
- code_level_traceability_oracle: NOT EVALUATED (No source code repository under analysis)
- dynamic_runtime_latency_oracle: NOT EVALUATED (Pipeline runs offline)
