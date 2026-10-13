import json
from pathlib import Path
from collections import Counter

bench_dir = Path("evaluation/multi_project/benchmark")
for d in sorted(bench_dir.iterdir()):
    gp = d / "gold_reference.json"
    if gp.is_file():
        data = json.load(open(gp, encoding="utf-8"))
        counts = Counter(data.get("expected_module_assignments", {}).values())
        total = len(data.get("expected_module_assignments", {}))
        print(f"=== {d.name} ({total} reqs) ===")
        for k, v in counts.most_common():
            print(f"  {k}: {v} ({v/total*100:.1f}%)")
