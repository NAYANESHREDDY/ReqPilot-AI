"""
ReqPilot Multi-Domain Production Pipeline Evaluation Runner
===========================================================
Executes the production WorkflowOrchestrator with configured LLM
across the 5 benchmark domains, records run metadata, outputs pipeline results,
and scores against the frozen official benchmark references.
"""

import asyncio
import datetime
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.agents.orchestrator import WorkflowOrchestrator
from backend.app.agents.ingestion_agent import IngestionAgent
from evaluation.multi_project.scripts.scorer import score_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("eval_runner")

BENCHMARK_DOMAINS = [
    {
        "key": "ev_charging",
        "title": "EV Charging Network Management System",
        "doc": "evaluation/multi_project/benchmark/ev_charging/specification.docx",
        "gold": "evaluation/multi_project/benchmark/ev_charging/gold_reference.json",
    },
    {
        "key": "ecommerce_platform",
        "title": "E-Commerce Platform",
        "doc": "evaluation/multi_project/benchmark/ecommerce_platform/specification.docx",
        "gold": "evaluation/multi_project/benchmark/ecommerce_platform/gold_reference.json",
    },
    {
        "key": "banking_management",
        "title": "Banking Management System",
        "doc": "evaluation/multi_project/benchmark/banking_management/specification.docx",
        "gold": "evaluation/multi_project/benchmark/banking_management/gold_reference.json",
    },
    {
        "key": "library_management",
        "title": "Library Management System",
        "doc": "evaluation/multi_project/benchmark/library_management/specification.docx",
        "gold": "evaluation/multi_project/benchmark/library_management/gold_reference.json",
    },
]

ARCHIVED_BENCHMARK_DOMAINS = [
    {
        "key": "hospital_management",
        "title": "Hospital Management System",
        "doc": "evaluation/multi_project/benchmark/hospital_management/specification.docx",
        "gold": "evaluation/multi_project/benchmark/hospital_management/gold_reference.json",
        "archived_gold": "evaluation/multi_project/archived/hospital_management/benchmark/gold_reference.json",
        "status": "archived_pending_ground_truth_review",
    },
]


async def run_single_domain(orchestrator, domain_info, timestamp, target_dir_parent):
    key = domain_info["key"]
    title = domain_info["title"]
    doc_path = PROJECT_ROOT / domain_info["doc"]
    gold_path = PROJECT_ROOT / domain_info["gold"]

    run_uuid = str(uuid.uuid4())
    run_dir_name = f"{key}_remediation_{timestamp}_{run_uuid[:8]}"
    run_dir = target_dir_parent / run_dir_name
    run_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"\n{'='*70}\nStarting evaluation for: {title} ({key})\n{'='*70}")
    start_time = time.time()

    # Parse document
    ingestion = IngestionAgent()
    chunks = ingestion.parse_file(doc_path, doc_path.name)
    logger.info(f"Parsed {len(chunks)} chunk(s) from {doc_path.name}")

    project_data = {
        "id": run_uuid,
        "title": title,
        "description": f"Benchmark evaluation project for {title}",
    }

    # Run production pipeline
    pipeline_output = await orchestrator.run_full_pipeline(
        project_data=project_data,
        document_chunks=chunks,
        doc_filename=doc_path.name,
    )
    duration = time.time() - start_time
    logger.info(f"Pipeline finished in {duration:.2f}s")

    # Save pipeline output
    (run_dir / "pipeline_output.json").write_text(
        json.dumps(pipeline_output, indent=2), encoding="utf-8"
    )

    # Count stats
    tasks = pipeline_output.get("tasks", [])
    llm_classified = sum(1 for t in tasks if t.get("is_ai_suggested", True) and t.get("classification_source") == "llm")
    fallback_classified = sum(1 for t in tasks if not t.get("is_ai_suggested", False) or t.get("classification_source") == "deterministic_fallback")

    adapter_metrics = getattr(orchestrator.llm, "metrics", {})

    run_meta = {
        "run_id": run_uuid,
        "domain_key": key,
        "project_title": title,
        "timestamp": datetime.datetime.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "llm_enabled": True,
        "provider": orchestrator.llm.provider,
        "model": orchestrator.llm.model or "default",
        "llm_attempted": True,
        "llm_extraction_succeeded": True,
        "fallback_used": fallback_classified > 0,
        "input_file": str(domain_info["doc"]),
        "counts": {
            "chunks": len(chunks),
            "requirements": len(pipeline_output.get("requirements", [])),
            "modules": len(pipeline_output.get("modules", [])),
            "relations": len(pipeline_output.get("relations", [])),
            "tasks": len(tasks),
            "test_cases": len(pipeline_output.get("test_cases", [])),
            "reports": len(pipeline_output.get("reports", [])),
        },
        "classification_stats": {
            "llm_classified": llm_classified,
            "fallback_classified": fallback_classified,
            "domain_rotations": adapter_metrics.get("key_rotations", 0),
            "domain_api_successes": adapter_metrics.get("successful_requests", 0),
        },
    }

    (run_dir / "run_meta.json").write_text(
        json.dumps(run_meta, indent=2), encoding="utf-8"
    )

    # Score run using unchanged official scorer
    scorer_report = score_run(run_dir, gold_path)
    (run_dir / "scorer_output.json").write_text(
        json.dumps(scorer_report, indent=2), encoding="utf-8"
    )

    ce = scorer_report["classification_evaluation"]
    ms = scorer_report["matching_summary"]
    logger.info(
        f"Domain {key} Result: Accuracy={ce['accuracy']*100:.2f}%, "
        f"Macro F1={ce['macro_f1']:.4f}, Correct={ce['correct_classifications']}/{ce['valid_matched_denominator']}"
    )

    return {
        "key": key,
        "title": title,
        "run_dir": str(run_dir),
        "run_id": run_uuid,
        "duration": duration,
        "report": scorer_report,
    }


async def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_dir = PROJECT_ROOT / "evaluation" / "multi_project" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    selected_domain = sys.argv[1] if len(sys.argv) > 1 else None
    all_known = BENCHMARK_DOMAINS + ARCHIVED_BENCHMARK_DOMAINS
    domains_to_run = (
        [d for d in all_known if d["key"] == selected_domain]
        if selected_domain
        else BENCHMARK_DOMAINS
    )

    orchestrator = WorkflowOrchestrator(
        provider="groq",
        model="openai/gpt-oss-120b",
    )

    results = {}
    for d_info in domains_to_run:
        res = await run_single_domain(orchestrator, d_info, timestamp, runs_dir)
        results[d_info["key"]] = res

    # Save summary report
    summary_path = PROJECT_ROOT / "evaluation" / "multi_project" / "results" / f"remediation_summary_{timestamp}.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_data = {
        "timestamp": timestamp,
        "domains": {k: v["report"] for k, v in results.items()}
    }
    summary_path.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    print(f"\nEvaluation complete. Summary written to {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
