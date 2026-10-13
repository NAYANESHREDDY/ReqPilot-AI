# Evaluation Report: E-Commerce Platform (ecommerce_platform)

## Run Information
- **Run ID**: 1e2d6f1a-9e01-4031-82fc-d55c2ef7289f
- **Timestamp**: 2026-10-12T17:14:44.471114
- **Provider / Model**: groq / openai/gpt-oss-120b
- **LLM Extraction Succeeded**: False
- **Deterministic Fallback Used**: True

## Content-Grounded Requirement Matching
- **Predicted Requirements**: 37
- **Reference Requirements**: 36
- **Uniquely Matched Pairs**: 36
- **Unmatched Predictions**: 1
- **Ambiguous Predictions**: 0
- **Duplicate Gold Matches**: 0
- **Unmatched Reference Entries**: 0

## Semantic Classification Metrics (On Matched Requirements)
- **Matched Denominator**: 36
- **Correct Classifications**: 16
- **Accuracy**: 44.44%
- **Macro Precision**: 0.3762
- **Macro Recall**: 0.3194
- **Macro F1**: 0.3356

### Per-Module Breakdown
| Module | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| AUTHENTICATION | 4 | 1 | 2 | 0.8 | 0.6667 | 0.7273 |
| BOOKING | 0 | 0 | 5 | 0.0 | 0.0 | 0.0 |
| CART MANAGEMENT | 0 | 1 | 0 | 0.0 | 0.0 | 0.0 |
| DATA | 0 | 0 | 8 | 0.0 | 0.0 | 0.0 |
| FILE | 0 | 0 | 1 | 0.0 | 0.0 | 0.0 |
| GATEWAY | 0 | 1 | 0 | 0.0 | 0.0 | 0.0 |
| NOTIFICATION | 4 | 0 | 0 | 1.0 | 1.0 | 1.0 |
| ORDER MANAGEMENT | 0 | 9 | 0 | 0.0 | 0.0 | 0.0 |
| PAYMENT | 5 | 2 | 0 | 0.7143 | 1.0 | 0.8333 |
| PROFILE | 0 | 0 | 2 | 0.0 | 0.0 | 0.0 |
| REPORTING | 2 | 0 | 1 | 1.0 | 0.6667 | 0.8 |
| SEARCH | 1 | 0 | 1 | 1.0 | 0.5 | 0.6667 |

### Classification Errors (20 total)
- **NFR-001 -> FR-003** (Customers should be able to view real-time product...): Expected DATA, Predicted GATEWAY
- **FR-004 -> FR-004** (Customers should be able to add products to a pers...): Expected BOOKING, Predicted CART MANAGEMENT
- **FR-005 -> FR-005** (Customers should be able to save items to a person...): Expected PROFILE, Predicted ORDER MANAGEMENT
- **FR-006 -> FR-006** (Customers should be able to proceed through a mult...): Expected BOOKING, Predicted ORDER MANAGEMENT
- **FR-009 -> FR-009** (Customers should be able to view their complete or...): Expected DATA, Predicted ORDER MANAGEMENT
- **FR-010 -> FR-010** (Customers should be able to request an order cance...): Expected BOOKING, Predicted ORDER MANAGEMENT
- **FR-011 -> FR-011** (Customers should be able to submit product reviews...): Expected PROFILE, Predicted ORDER MANAGEMENT
- **FR-013 -> FR-013** (Vendors should be able to create, update, and mana...): Expected DATA, Predicted UNASSIGNED
- **FR-014 -> FR-014** (Vendors should be able to set base prices, promoti...): Expected DATA, Predicted UNASSIGNED
- **FR-016 -> FR-016** (Vendors should be able to view pending orders and ...): Expected BOOKING, Predicted ORDER MANAGEMENT

## Structural Integrity Checks
- **Total Requirements**: 37
- **Requirements with Assigned Tasks**: 37 (100.0%)
- **Total Modules**: 11
- **Total Architecture Relations**: 23
- **Total Test Cases**: 37
- **Untested Requirements**: 0

## Declared Non-Evaluated Metrics
- semantic_test_step_oracle: NOT EVALUATED (No independent ground-truth test assertions)
- code_level_traceability_oracle: NOT EVALUATED (No source code repository under analysis)
- dynamic_runtime_latency_oracle: NOT EVALUATED (Pipeline runs offline)
