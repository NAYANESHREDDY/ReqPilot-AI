# Evaluation Report: Banking Management System (banking_management)

## Run Information
- **Run ID**: ba26cb8e-814b-44d7-bf55-3e7e3e7f9f44
- **Timestamp**: 2026-10-12T17:17:13.132526
- **Provider / Model**: groq / openai/gpt-oss-120b
- **LLM Extraction Succeeded**: True
- **Deterministic Fallback Used**: False

## Content-Grounded Requirement Matching
- **Predicted Requirements**: 25
- **Reference Requirements**: 25
- **Uniquely Matched Pairs**: 25
- **Unmatched Predictions**: 0
- **Ambiguous Predictions**: 0
- **Duplicate Gold Matches**: 0
- **Unmatched Reference Entries**: 0

## Semantic Classification Metrics (On Matched Requirements)
- **Matched Denominator**: 25
- **Correct Classifications**: 9
- **Accuracy**: 36.0%
- **Macro Precision**: 0.5
- **Macro Recall**: 0.3583
- **Macro F1**: 0.3979

### Per-Module Breakdown
| Module | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| AUTHENTICATION | 3 | 0 | 3 | 1.0 | 0.5 | 0.6667 |
| BOOKING | 0 | 2 | 2 | 0.0 | 0.0 | 0.0 |
| DATA | 1 | 2 | 4 | 0.3333 | 0.2 | 0.25 |
| FILE | 2 | 1 | 0 | 0.6667 | 1.0 | 0.8 |
| NOTIFICATION | 1 | 0 | 1 | 1.0 | 0.5 | 0.6667 |
| PAYMENT | 0 | 6 | 4 | 0.0 | 0.0 | 0.0 |
| PROFILE | 0 | 0 | 1 | 0.0 | 0.0 | 0.0 |
| REPORTING | 2 | 0 | 1 | 1.0 | 0.6667 | 0.8 |

### Classification Errors (16 total)
- **FR-002 -> FR-002** (View account balances and transaction history...): Expected DATA, Predicted PAYMENT
- **FR-003 -> FR-003** (Initiate domestic fund transfers...): Expected PAYMENT, Predicted UNASSIGNED
- **FR-004 -> FR-004** (Customers should be able to schedule recurring sta...): Expected PAYMENT, Predicted BOOKING
- **FR-005 -> FR-005** (Online loan application for personal, vehicle, or ...): Expected BOOKING, Predicted UNASSIGNED
- **FR-007 -> FR-007** (Debit card activation, temporary freeze, and limit...): Expected PROFILE, Predicted DATA
- **FR-009 -> FR-009** (Report suspicious transactions or compromised cred...): Expected NOTIFICATION, Predicted PAYMENT
- **FR-011 -> FR-011** (Tellers should be able to process cash deposits an...): Expected PAYMENT, Predicted UNASSIGNED
- **FR-012 -> FR-012** (Tellers should be able to verify customer signatur...): Expected AUTHENTICATION, Predicted FILE
- **FR-013 -> FR-013** (Tellers should be able to issue cashier checks and...): Expected PAYMENT, Predicted UNASSIGNED
- **FR-017 -> FR-016** (Loan officers should be able to calculate debt-to-...): Expected REPORTING, Predicted BOOKING

## Structural Integrity Checks
- **Total Requirements**: 25
- **Requirements with Assigned Tasks**: 25 (100.0%)
- **Total Modules**: 8
- **Total Architecture Relations**: 15
- **Total Test Cases**: 25
- **Untested Requirements**: 0

## Declared Non-Evaluated Metrics
- semantic_test_step_oracle: NOT EVALUATED (No independent ground-truth test assertions)
- code_level_traceability_oracle: NOT EVALUATED (No source code repository under analysis)
- dynamic_runtime_latency_oracle: NOT EVALUATED (Pipeline runs offline)
