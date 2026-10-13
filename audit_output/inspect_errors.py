import json
from pathlib import Path

runs_dir = Path("evaluation/multi_project/runs")
domains = ["library_management", "banking_management", "ecommerce_platform", "ev_charging", "hospital_management"]

for d in domains:
    matching_runs = [p for p in runs_dir.iterdir() if p.is_dir() and p.name.startswith(d + "_remediation_")]
    if not matching_runs:
        matching_runs = [p for p in runs_dir.iterdir() if p.is_dir() and p.name.startswith(d)]
    
    matching_runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if matching_runs:
        latest = matching_runs[0]
        sc_path = latest / "scorer_output.json"
        if sc_path.exists():
            sc = json.load(open(sc_path, encoding="utf-8"))
            cls_eval = sc.get("classification_evaluation", {})
            acc = cls_eval.get("accuracy", 0) * 100
            correct = cls_eval.get("correct_classifications")
            denom = cls_eval.get("valid_matched_denominator")
            f1 = cls_eval.get("macro_f1", 0)
            print(f"=== {d} ({latest.name}) ===")
            print(f"Accuracy: {acc:.2f}%, Correct: {correct}/{denom}, Macro F1: {f1:.4f}")
            errors = cls_eval.get("errors_sample", [])
            print(f"Total Errors: {len(errors)}")
            for e in errors:
                pred_id = e.get("pred_id")
                exp = e.get("expected")
                pred = e.get("predicted")
                text = e.get("summary", "")[:75]
                print(f"  [{pred_id}] Expected: {exp:18} | Predicted: {pred:18} | {text}")
            print()
