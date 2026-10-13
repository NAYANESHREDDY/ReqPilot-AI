import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter

from backend.app.agents.ambiguity_agent import AmbiguityAgent
from backend.app.agents.conflict_agent import ConflictAgent
from backend.app.agents.duplicate_agent import DuplicateAgent
from backend.app.agents.llm_adapter import LLMAdapter
from backend.app.schemas import (
    EvaluationResultResponse,
    EvaluationMetric,
    BaselineComparison,
)

router = APIRouter(tags=["evaluation"])

BENCHMARK_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "evaluation"
    / "benchmark_cases.json"
)


def _empty_metric() -> EvaluationMetric:
    """Metric placeholder for a benchmark dimension not represented in the dataset."""
    return EvaluationMetric(
        precision=0.0,
        recall=0.0,
        f1_score=0.0,
        accuracy=0.0,
        total_samples=0,
    )


def _positive_detection_metric(detected: int, total: int) -> EvaluationMetric:
    """
    The benchmark contains positive examples only.

    Therefore we report positive-case detection rate through all four
    metric fields for backward compatibility with the existing frontend.
    This is NOT a conventional precision/recall/F1 classification benchmark.
    """
    rate = detected / total if total else 0.0

    return EvaluationMetric(
        precision=rate,
        recall=rate,
        f1_score=rate,
        accuracy=rate,
        total_samples=total,
    )


async def _evaluate_conflicts(cases):
    agent = ConflictAgent(LLMAdapter(api_key=None))

    total = 0
    detected = 0

    for case in cases:
        if case.get("category") != "conflict":
            continue

        total += 1

        req_a = {
            "id": f"{case['id']}-A",
            "summary": case["statement_a"],
            "description": "",
        }
        req_b = {
            "id": f"{case['id']}-B",
            "summary": case["statement_b"],
            "description": "",
        }

        predictions = await agent.detect_conflicts([req_a, req_b])

        if predictions:
            detected += 1

    return _positive_detection_metric(detected, total)


def _evaluate_ambiguity(cases):
    agent = AmbiguityAgent()

    total = 0
    detected = 0

    for case in cases:
        if case.get("category") != "ambiguity":
            continue

        total += 1

        requirement = {
            "id": case["id"],
            "summary": case["text"],
            "description": "",
        }

        predictions = agent.detect_ambiguities([requirement])

        expected = {
            str(item).lower().strip()
            for item in case.get("expected_ambiguities", [])
        }

        actual = {
            str(item.get("detected_phrase", "")).lower().strip()
            for item in predictions
            if item.get("detected_phrase")
        }

        if expected.issubset(actual):
            detected += 1

    return _positive_detection_metric(detected, total)


def _evaluate_duplicates(cases):
    agent = DuplicateAgent()

    total = 0
    detected = 0

    for case in cases:
        if case.get("category") != "duplicate":
            continue

        total += 1

        req_a = {
            "id": f"{case['id']}-A",
            "summary": case["statement_a"],
            "description": "",
        }
        req_b = {
            "id": f"{case['id']}-B",
            "summary": case["statement_b"],
            "description": "",
        }

        predictions = agent.detect_duplicates([req_a, req_b])

        if predictions:
            detected += 1

    return _positive_detection_metric(detected, total)


@router.get("/api/evaluation/run", response_model=EvaluationResultResponse)
async def run_evaluation_benchmarks():
    """
    Runs the reproducible benchmark dataset against the implemented
    ambiguity, conflict, and duplicate detection agents.

    The current benchmark does not contain requirement-extraction,
    traceability, baseline, hallucination, or latency ground truth.
    Those dimensions therefore remain explicitly unevaluated.
    """

    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(
            f"Evaluation benchmark not found: {BENCHMARK_PATH}"
        )

    with BENCHMARK_PATH.open("r", encoding="utf-8") as file:
        benchmark = json.load(file)

    cases = benchmark.get("test_cases", [])

    ambiguity_metric = _evaluate_ambiguity(cases)
    conflict_metric = await _evaluate_conflicts(cases)
    duplicate_metric = _evaluate_duplicates(cases)

    # The current benchmark contains no extraction ground truth.
    requirement_extraction_metric = _empty_metric()

    # The current benchmark contains no traceability ground truth.
    traceability_coverage_pct = 0.0

    # No independently implemented baseline systems are available in the
    # repository, so no baseline comparison is reported.
    baseline_comparisons = []

    return {
        "requirement_extraction": requirement_extraction_metric,
        "ambiguity_detection": ambiguity_metric,
        "conflict_detection": conflict_metric,
        "duplicate_detection": duplicate_metric,
        "traceability_coverage_pct": traceability_coverage_pct,
        "baseline_comparisons": baseline_comparisons,
        "tested_at": datetime.now(timezone.utc),
    }