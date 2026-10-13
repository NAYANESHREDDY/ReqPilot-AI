"""
Held-Out Logistics Evaluation Runner
====================================
Runs the production WorkflowOrchestrator against the held-out
Warehouse Logistics & Fleet Dispatch System benchmark and scores it
with the official unmodified scorer.
"""

import asyncio
import datetime
import json
import logging
import time
import uuid
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.agents.orchestrator import WorkflowOrchestrator
from backend.app.agents.ingestion_agent import IngestionAgent
from evaluation.multi_project.scripts.scorer import score_run

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("held_out_eval")


async def run_held_out():
    bench_dir = PROJECT_ROOT / "evaluation" / "multi_project" / "benchmark" / "held_out_logistics"
    doc_path = bench_dir / "specification.docx"
    gold_path = bench_dir / "gold_reference.json"

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_uuid = str(uuid.uuid4())
    run_dir = PROJECT_ROOT / "evaluation" / "multi_project" / "runs" / f"held_out_logistics_{timestamp}_{run_uuid[:8]}"
    run_dir.mkdir(parents=True, exist_ok=True)

    title = "Warehouse Logistics & Fleet Dispatch System"
    logger.info(f"Starting held-out evaluation for: {title}")
    start_time = time.time()

    ingestion = IngestionAgent()
    chunks = ingestion.parse_file(doc_path, doc_path.name)
    logger.info(f"Parsed {len(chunks)} chunk(s) from {doc_path.name}")

    orchestrator = WorkflowOrchestrator(
        provider="groq",
        model="openai/gpt-oss-120b",
    )

    project_data = {
        "id": run_uuid,
        "title": title,
        "description": f"Held-out benchmark evaluation for {title}",
    }

    pipeline_output = await orchestrator.run_full_pipeline(
        project_data=project_data,
        document_chunks=chunks,
        doc_filename=doc_path.name,
    )
    duration = time.time() - start_time
    logger.info(f"Pipeline finished in {duration:.2f}s")

    (run_dir / "pipeline_output.json").write_text(json.dumps(pipeline_output, indent=2), encoding="utf-8")

    tasks = pipeline_output.get("tasks", [])
    llm_classified = sum(1 for t in tasks if t.get("is_ai_suggested", True) and t.get("classification_source") == "llm")
    fallback_classified = sum(1 for t in tasks if not t.get("is_ai_suggested", False) or t.get("classification_source") == "deterministic_fallback")
    adapter_metrics = getattr(orchestrator.llm, "metrics", {})

    run_meta = {
        "run_id": run_uuid,
        "domain_key": "held_out_logistics",
        "project_title": title,
        "timestamp": datetime.datetime.now().isoformat(),
        "duration_seconds": round(duration, 2),
        "llm_enabled": True,
        "provider": orchestrator.llm.provider,
        "model": orchestrator.llm.model or "default",
        "llm_attempted": True,
        "llm_extraction_succeeded": True,
        "fallback_used": fallback_classified > 0,
        "input_file": str(doc_path),
        "counts": {
            "chunks": len(chunks),
            "requirements": len(pipeline_output.get("requirements", [])),
            "modules": len(pipeline_output.get("modules", [])),
            "relations": len(pipeline_output.get("relations", [])),
            "tasks": len(tasks),
        },
        "classification_stats": {
            "llm_classified": llm_classified,
            "fallback_classified": fallback_classified,
            "domain_rotations": adapter_metrics.get("key_rotations", 0),
            "domain_api_successes": adapter_metrics.get("successful_requests", 0),
        },
    }
    (run_dir / "run_meta.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

    scorer_report = score_run(run_dir, gold_path)
    (run_dir / "scorer_output.json").write_text(json.dumps(scorer_report, indent=2), encoding="utf-8")

    ce = scorer_report["classification_evaluation"]
    logger.info(
        f"Held-Out Result: Accuracy={ce['accuracy']*100:.2f}%, "
        f"Macro F1={ce['macro_f1']:.4f}, Correct={ce['correct_classifications']}/{ce['valid_matched_denominator']}"
    )
    return scorer_report


if __name__ == "__main__":
    asyncio.run(run_held_out())
