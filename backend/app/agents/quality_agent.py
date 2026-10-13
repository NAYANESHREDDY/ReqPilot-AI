from typing import Dict, Any, List
from backend.app.config import settings

class QualityAgent:
    """Agent 8.4: Requirement Quality Agent
    Evaluates requirements across 7 transparent dimensions defined in Section 10 of the Blueprint:
    Completeness, Clarity, Atomicity, Consistency, Testability, Feasibility, Traceability.
    Produces weighted quality scores and dimension-level breakdowns.
    """

    def __init__(self):
        self.weights = settings.QUALITY_WEIGHTS

    def evaluate_requirement(self, req: Dict[str, Any], all_reqs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        completeness = self._score_completeness(req)
        clarity = self._score_clarity(req)
        atomicity = self._score_atomicity(req)
        consistency = self._score_consistency(req, all_reqs or [])
        testability = self._score_testability(req)
        feasibility = self._score_feasibility(req)
        traceability = self._score_traceability(req)

        breakdown = {
            "completeness": round(completeness, 1),
            "clarity": round(clarity, 1),
            "atomicity": round(atomicity, 1),
            "consistency": round(consistency, 1),
            "testability": round(testability, 1),
            "feasibility": round(feasibility, 1),
            "traceability": round(traceability, 1),
        }

        total_score = (
            self.weights["completeness"] * completeness +
            self.weights["clarity"] * clarity +
            self.weights["atomicity"] * atomicity +
            self.weights["consistency"] * consistency +
            self.weights["testability"] * testability +
            self.weights["feasibility"] * feasibility +
            self.weights["traceability"] * traceability
        )

        return {
            "quality_score": round(total_score, 1),
            "breakdown": breakdown,
        }

    def _score_completeness(self, req: Dict[str, Any]) -> float:
        score = 40.0
        if req.get("actor") and req["actor"] != "User":
            score += 15.0
        if req.get("action"):
            score += 15.0
        if req.get("target_object"):
            score += 10.0
        if req.get("expected_outcome"):
            score += 10.0
        if req.get("acceptance_criteria") and len(req["acceptance_criteria"]) > 0:
            score += 10.0
        return min(100.0, score)

    def _score_clarity(self, req: Dict[str, Any]) -> float:
        desc = (req.get("description", "") + " " + req.get("summary", "")).lower()
        vague_words = ["fast", "user-friendly", "secure", "efficient", "appropriate", "reasonable", "simple", "flexible", "soon"]
        penalty = sum(15.0 for word in vague_words if word in desc)
        return max(30.0, 100.0 - penalty)

    def _score_atomicity(self, req: Dict[str, Any]) -> float:
        desc = req.get("description", "")
        # Penalize sentences joining multiple disparate requirements with "and also", "as well as", multiple semicolons
        conjunctions = desc.count(" and ") + desc.count(" as well as ") + desc.count(";")
        if conjunctions > 3:
            return 50.0
        elif conjunctions > 1:
            return 75.0
        return 95.0

    def _score_consistency(self, req: Dict[str, Any], all_reqs: List[Dict[str, Any]]) -> float:
        # Default high, gets discounted if marked in conflict by ConflictAgent
        return 90.0

    def _score_testability(self, req: Dict[str, Any]) -> float:
        desc = (req.get("description", "") + " " + req.get("summary", "")).lower()
        has_metrics = any(char.isdigit() for char in desc) or any(w in desc for w in ["seconds", "ms", "%", "hours", "status", "http", "code"])
        has_criteria = bool(req.get("acceptance_criteria"))
        if has_metrics and has_criteria:
            return 95.0
        elif has_metrics or has_criteria:
            return 80.0
        return 60.0

    def _score_feasibility(self, req: Dict[str, Any]) -> float:
        desc = req.get("description", "").lower()
        if any(unrealistic in desc for unrealistic in ["100% uptime", "zero latency", "infinite", "instantaneous", "zero error"]):
            return 40.0
        return 90.0

    def _score_traceability(self, req: Dict[str, Any]) -> float:
        if req.get("source_id") and req.get("source_excerpt"):
            return 100.0
        elif req.get("source_id"):
            return 70.0
        return 30.0
