# Evaluation Report: Library Management System (library_management)

## Run Information
- **Run ID**: 037fa230-720d-4216-98b5-a417d7c023e4
- **Timestamp**: 2026-10-12T17:20:17.121585
- **Provider / Model**: groq / openai/gpt-oss-120b
- **LLM Extraction Succeeded**: False
- **Deterministic Fallback Used**: True

## Content-Grounded Requirement Matching
- **Predicted Requirements**: 24
- **Reference Requirements**: 24
- **Uniquely Matched Pairs**: 24
- **Unmatched Predictions**: 0
- **Ambiguous Predictions**: 0
- **Duplicate Gold Matches**: 0
- **Unmatched Reference Entries**: 0

## Semantic Classification Metrics (On Matched Requirements)
- **Matched Denominator**: 24
- **Correct Classifications**: 16
- **Accuracy**: 66.67%
- **Macro Precision**: 0.7778
- **Macro Recall**: 0.6151
- **Macro F1**: 0.6679

### Per-Module Breakdown
| Module | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| AUTHENTICATION | 3 | 0 | 1 | 1.0 | 0.75 | 0.8571 |
| BOOKING | 5 | 0 | 1 | 1.0 | 0.8333 | 0.9091 |
| DATA | 2 | 0 | 5 | 1.0 | 0.2857 | 0.4444 |
| GATEWAY | 0 | 1 | 0 | 0.0 | 0.0 | 0.0 |
| NOTIFICATION | 1 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| ORDER MANAGEMENT | 0 | 1 | 0 | 0.0 | 0.0 | 0.0 |
| PAYMENT | 2 | 0 | 1 | 1.0 | 0.6667 | 0.8 |
| REPORTING | 2 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| SEARCH | 1 | 0 | 0 | 1.0 | 1.0 | 1.0 |

### Classification Errors (8 total)
- **NFR-001 -> FR-003** (Patrons should be able to view real-time catalog a...): Expected DATA, Predicted GATEWAY
- **FR-004 -> FR-005** (Patrons should be able to view their active borrow...): Expected DATA, Predicted UNASSIGNED
- **FR-008 -> FR-009** (Patrons should be able to submit purchase recommen...): Expected BOOKING, Predicted ORDER MANAGEMENT
- **FR-009 -> FR-010** (Circulation Desk Staff Requirements Circulation st...): Expected AUTHENTICATION, Predicted UNASSIGNED
- **FR-011 -> FR-012** (Circulation staff should be able to process return...): Expected DATA, Predicted UNASSIGNED
- **FR-012 -> FR-013** (The system should automatically calculate late fee...): Expected PAYMENT, Predicted UNASSIGNED
- **FR-016 -> FR-017** (Catalogers should be able to manage inventory copi...): Expected DATA, Predicted UNASSIGNED
- **FR-018 -> FR-019** (Catalogers should be able to conduct periodic phys...): Expected DATA, Predicted UNASSIGNED

## Structural Integrity Checks
- **Total Requirements**: 24
- **Requirements with Assigned Tasks**: 24 (100.0%)
- **Total Modules**: 10
- **Total Architecture Relations**: 21
- **Total Test Cases**: 24
- **Untested Requirements**: 0

## Declared Non-Evaluated Metrics
- semantic_test_step_oracle: NOT EVALUATED (No independent ground-truth test assertions)
- code_level_traceability_oracle: NOT EVALUATED (No source code repository under analysis)
- dynamic_runtime_latency_oracle: NOT EVALUATED (Pipeline runs offline)
