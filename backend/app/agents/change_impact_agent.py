from typing import List, Dict, Any
import re


class ChangeImpactAgent:
    """
    Evidence-based change impact analysis.

    Determines the blast radius of a requirement change from the
    actual relationships supplied to the agent:

        Requirement
            -> Tasks
            -> Architecture Modules
            -> Test Cases

    Related requirements are detected using deterministic textual
    similarity rather than domain-specific keywords.

    No synthetic artifacts, domain-specific assumptions, or fabricated
    impact relationships are introduced.
    """

    def analyze_change(
        self,
        target_req_id: str,
        new_summary: str,
        new_description: str,
        all_requirements: List[Dict[str, Any]],
        all_modules: List[Dict[str, Any]],
        all_tasks: List[Dict[str, Any]],
        all_tests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        impact_items: List[Dict[str, Any]] = []

        target_req = next(
            (
                r for r in all_requirements
                if r.get("id") == target_req_id
            ),
            None,
        )

        if target_req is None:
            raise ValueError(
                f"Requirement '{target_req_id}' was not found."
            )

        original_summary = target_req.get("summary", "")
        original_description = target_req.get("description", "")

        # ---------------------------------------------------------
        # 1. Directly affected tasks
        # ---------------------------------------------------------

        affected_tasks = [
            t
            for t in all_tasks
            if t.get("requirement_id") == target_req_id
        ]

        for task in affected_tasks:
            complexity = str(
                task.get("complexity") or "medium"
            ).lower()

            if complexity == "high":
                severity = "high"
            elif complexity == "low":
                severity = "low"
            else:
                severity = "medium"

            impact_items.append(
                {
                    "artifact_type": "task",
                    "artifact_id": task.get("id"),
                    "artifact_name": task.get("title", ""),
                    "impact_description": (
                        "Task is directly linked to the changed "
                        "requirement and should be reviewed for "
                        "implementation and acceptance-criteria changes."
                    ),
                    "severity": severity,
                }
            )

        # ---------------------------------------------------------
        # 2. Directly affected tests
        # ---------------------------------------------------------

        affected_tests = [
            test
            for test in all_tests
            if test.get("requirement_id") == target_req_id
        ]

        for test in affected_tests:
            impact_items.append(
                {
                    "artifact_type": "test",
                    "artifact_id": test.get("id"),
                    "artifact_name": test.get("title", ""),
                    "impact_description": (
                        "Test case is directly linked to the changed "
                        "requirement and should be reviewed against "
                        "the proposed requirement."
                    ),
                    "severity": "medium",
                }
            )

        # ---------------------------------------------------------
        # 3. Directly affected architecture modules
        # ---------------------------------------------------------

        module_map = {
            module.get("id"): module
            for module in all_modules
            if module.get("id")
        }

        module_ids = {
            task.get("module_id")
            for task in affected_tasks
            if task.get("module_id")
        }

        for module_id in sorted(module_ids):
            module = module_map.get(module_id)

            if module is None:
                continue

            responsibilities = module.get(
                "responsibilities"
            ) or []

            evidence = []

            if responsibilities:
                evidence.append(
                    "Responsibilities: "
                    + "; ".join(
                        str(value)
                        for value in responsibilities
                    )
                )

            if module.get("tech_stack"):
                evidence.append(
                    f"Technology evidence: {module['tech_stack']}"
                )

            evidence_text = " ".join(evidence)

            description = (
                "Module is referenced by a task directly linked "
                "to the changed requirement and should be reviewed."
            )

            if evidence_text:
                description += f" {evidence_text}."

            impact_items.append(
                {
                    "artifact_type": "module",
                    "artifact_id": module_id,
                    "artifact_name": module.get("name", module_id),
                    "impact_description": description,
                    "severity": "high",
                }
            )

        # ---------------------------------------------------------
        # 4. Related requirements
        # ---------------------------------------------------------

        old_text = self._normalize_text(
            f"{original_summary} {original_description}"
        )

        new_text = self._normalize_text(
            f"{new_summary} {new_description}"
        )

        old_tokens = self._tokens(old_text)
        new_tokens = self._tokens(new_text)

        changed_tokens = (
            old_tokens.symmetric_difference(new_tokens)
        )

        related_requirements = []

        for requirement in all_requirements:
            req_id = requirement.get("id")

            if req_id == target_req_id:
                continue

            req_text = self._normalize_text(
                f"{requirement.get('summary', '')} "
                f"{requirement.get('description', '')}"
            )

            req_tokens = self._tokens(req_text)

            if not req_tokens:
                continue

            overlap_with_new = (
                len(new_tokens & req_tokens)
                / max(len(new_tokens), 1)
            )

            overlap_with_changed = (
                len(changed_tokens & req_tokens)
                / max(len(changed_tokens), 1)
            )

            # Require meaningful textual evidence.
            similarity = max(
                overlap_with_new,
                overlap_with_changed,
            )

            if similarity >= 0.30:
                related_requirements.append(
                    (
                        similarity,
                        requirement,
                    )
                )

        related_requirements.sort(
            key=lambda item: (
                -item[0],
                str(item[1].get("id", "")),
            )
        )

        for similarity, requirement in related_requirements:
            impact_items.append(
                {
                    "artifact_type": "requirement",
                    "artifact_id": requirement.get("id"),
                    "artifact_name": requirement.get(
                        "summary",
                        "",
                    ),
                    "impact_description": (
                        "Requirement has overlapping textual "
                        f"evidence with the proposed change "
                        f"(similarity {similarity:.2f}) and "
                        "should be reviewed for dependency or "
                        "business-rule effects."
                    ),
                    "severity": "medium",
                }
            )

        # ---------------------------------------------------------
        # 5. Risk assessment
        # ---------------------------------------------------------

        task_count = len(affected_tasks)
        test_count = len(affected_tests)
        module_count = len(module_ids)
        related_req_count = len(related_requirements)

        total_affected = len(impact_items)

        high_complexity_tasks = sum(
            1
            for task in affected_tasks
            if str(
                task.get("complexity") or ""
            ).lower()
            == "high"
        )

        if high_complexity_tasks >= 2 or total_affected >= 10:
            risk_level = "critical"
            schedule_impact = "High"
        elif (
            high_complexity_tasks >= 1
            or total_affected >= 5
        ):
            risk_level = "high"
            schedule_impact = "Medium"
        elif total_affected >= 2:
            risk_level = "medium"
            schedule_impact = "Low"
        else:
            risk_level = "low"
            schedule_impact = "Negligible"

        # ---------------------------------------------------------
        # 6. Return existing API contract
        # ---------------------------------------------------------

        return {
            "target_requirement_id": target_req_id,
            "title": (
                f"Change Request for {target_req_id}: "
                f"{new_summary[:50]}"
            ),
            "description": (
                f"Change requested from "
                f"'{original_summary}' to "
                f"'{new_summary}'."
            ),
            "proposed_summary": new_summary,
            "proposed_description": new_description,
            "risk_level": risk_level,
            "schedule_impact": schedule_impact,
            "summary_stats": {
                "affected_requirements": related_req_count,
                "affected_modules": module_count,
                "affected_tasks": task_count,
                "affected_tests": test_count,
                "total_artifacts": total_affected,
            },
            "impact_items": impact_items,
        }

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = str(text or "").lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _tokens(text: str) -> set[str]:
        stop_words = {
            "the",
            "a",
            "an",
            "shall",
            "should",
            "must",
            "will",
            "be",
            "to",
            "of",
            "and",
            "or",
            "for",
            "in",
            "on",
            "by",
            "with",
            "from",
            "as",
            "is",
            "are",
            "this",
            "that",
            "system",
        }

        return {
            token
            for token in text.split()
            if len(token) > 2
            and token not in stop_words
        }