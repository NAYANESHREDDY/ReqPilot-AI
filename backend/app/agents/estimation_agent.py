from typing import Dict, Any, List


class EstimationAgent:
    """
    Deterministic task estimation agent.

    Estimates effort from:
    - task complexity
    - acceptance-criteria count
    - task characteristics

    This is a deterministic baseline, not an AI confidence claim.
    """

    COMPLEXITY_MAP = {
        "low": {
            "base_hours": 6.0,
            "story_points": 2,
            "variance": 0.20,
        },
        "medium": {
            "base_hours": 12.0,
            "story_points": 3,
            "variance": 0.25,
        },
        "high": {
            "base_hours": 20.0,
            "story_points": 5,
            "variance": 0.35,
        },
        "critical": {
            "base_hours": 32.0,
            "story_points": 8,
            "variance": 0.40,
        },
    }

    def estimate_task(
        self,
        task: Dict[str, Any],
        criteria_count: int = 2,
    ) -> Dict[str, Any]:

        complexity = str(
            task.get("complexity", "medium")
        ).lower()

        config = self.COMPLEXITY_MAP.get(
            complexity,
            self.COMPLEXITY_MAP["medium"],
        )

        criteria_count = max(
            0,
            int(criteria_count or 0),
        )

        # Additional acceptance criteria increase implementation effort.
        extra_criteria = max(
            0,
            criteria_count - 2,
        ) * 1.5

        expected_hours = round(
            config["base_hours"] + extra_criteria,
            1,
        )

        variance = config["variance"]

        min_hours = round(
            expected_hours * (1 - variance),
            1,
        )

        max_hours = round(
            expected_hours * (1 + variance),
            1,
        )

        return {
            "story_points": config["story_points"],
            "expected_hours": expected_hours,
            "min_hours": min_hours,
            "max_hours": max_hours,
            "confidence_level": "deterministic baseline",
        }

    def estimate_tasks(
        self,
        tasks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Convenience method for estimating a collection of tasks.
        Does not mutate the supplied task dictionaries.
        """

        results = []

        for task in tasks:

            criteria = task.get(
                "acceptance_criteria",
                [],
            )

            if isinstance(criteria, list):
                criteria_count = len(criteria)
            elif criteria:
                criteria_count = 1
            else:
                criteria_count = 0

            estimate = self.estimate_task(
                task,
                criteria_count,
            )

            results.append(
                {
                    "task_id": task.get("id"),
                    **estimate,
                }
            )

        return results