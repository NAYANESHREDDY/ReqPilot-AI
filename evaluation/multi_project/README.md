# ReqPilot AI Multi-Project Ground-Truth Evaluation Benchmark

This directory (evaluation/multi_project/) contains a reproducible multi-domain ground-truth benchmark and scoring harness for the ReqPilot AI requirements analysis pipeline across four active software engineering domains:
1. **EV Charging Station Management System** (ev_charging)
2. **E-Commerce Platform** (ecommerce_platform)
3. **Banking Management System** (banking_management)
4. **Library Management System** (library_management)

*Note: Hospital Management System (`hospital_management`) was retired from the active benchmark suite and archived under `evaluation/multi_project/archived/hospital_management/` for independent ground-truth review.*

---

## Directory Structure

- benchmark/: DOCX, TXT, gold_reference.json, PROVENANCE.md for each active domain
- archived/: Historical benchmarks and assets archived from active evaluation
- manifest.json: SHA-256 hashes of all frozen active benchmark references
- runs/: Raw immutable pipeline outputs and run_meta.json for each run
- scripts/: scorer.py, generate_reports.py
- reports/: Project-level markdown reports
- results/: summary.csv, summary.json, final_report.md

---

## Reproducibility Command

To regenerate all scores and reports:
`powershell
python evaluation/multi_project/scripts/generate_reports.py
`
