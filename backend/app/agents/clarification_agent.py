from typing import List, Dict, Any

class ClarificationAgent:
    """Agent 8.8: Clarification Agent
    Transforms detected ambiguities, missing parameters, and open questions into actionable stakeholder inquiries.
    """

    def generate_clarification_questions(self, requirements: List[Dict[str, Any]], issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        questions = []
        for issue in issues:
            if issue.get("issue_type") == "ambiguity" and "question" in issue:
                questions.append({
                    "requirement_id": issue.get("requirement_id"),
                    "question": issue.get("question"),
                    "rationale": f"Clarifying ambiguous phrase: '{issue.get('detected_phrase')}'",
                    "priority": "high" if issue.get("severity") in ["high", "critical"] else "medium",
                    "suggested_options": issue.get("suggested_options", []),
                    "status": "pending",
                })
            elif issue.get("issue_type") == "conflict":
                questions.append({
                    "requirement_id": issue.get("requirement_id"),
                    "question": f"How should the conflict between {issue.get('requirement_id')} and {issue.get('conflict_with_id')} be resolved?",
                    "rationale": issue.get("description"),
                    "priority": "high",
                    "suggested_options": [
                        f"Enforce rule in {issue.get('requirement_id')}",
                        f"Enforce rule in {issue.get('conflict_with_id')}",
                        "Apply conditional compromise (e.g. 24h grace period)"
                    ],
                    "status": "pending",
                })

        # Also check for requirements with missing business rules (e.g., admin management)
        for req in requirements:
            summary = req.get("summary", "").lower()
            if "manage" in summary and "user" in summary and not any(q["requirement_id"] == req["id"] for q in questions):
                questions.append({
                    "requirement_id": req["id"],
                    "question": f"What specific administrative operations are permitted for {req.get('target_object', 'users')}?",
                    "rationale": "Requirement mentions management without defining CRUD boundaries or roles.",
                    "priority": "medium",
                    "suggested_options": [
                        "Can create, edit, deactivate, and view audit logs",
                        "Can deactivate but not permanently delete",
                        "Tiered roles: SuperAdmin, SupportAdmin, Auditor"
                    ],
                    "status": "pending",
                })

        return questions
