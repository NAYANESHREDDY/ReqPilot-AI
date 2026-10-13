from typing import List, Dict, Any


class ResourceMatchingAgent:
    """
    Requirement/architecture-driven resource matching agent.

    Matching formula:

        0.50 * SkillMatch
        + 0.25 * Availability
        + 0.25 * WorkloadFactor

    Skill requirements should come from the task or its associated
    architecture module.

    The agent does NOT invent technologies for unknown domains.
    """

    def rank_candidates_for_task(
        self,
        task: Dict[str, Any],
        team_members: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        required_skills = self._extract_required_skills(
            task
        )

        ranked = []

        for member in team_members:

            member_skills = self._normalize_skills(
                member.get("skills", {})
            )

            load_pct = self._safe_percentage(
                member.get(
                    "current_load_pct",
                    0.0,
                )
            )

            if required_skills:

                skill_scores = [
                    self._skill_match(
                        member_skills,
                        skill,
                    )
                    for skill in required_skills
                ]

                skill_match = (
                    sum(skill_scores)
                    / len(skill_scores)
                )

            else:
                # No technology/skill evidence means we cannot claim
                # a skill match. Use a neutral baseline rather than
                # inventing skills.
                skill_match = 50.0

            availability = max(
                0.0,
                100.0 - load_pct,
            )

            workload_factor = max(
                0.0,
                100.0 - load_pct,
            )

            total_match = (
                0.50 * skill_match
                + 0.25 * availability
                + 0.25 * workload_factor
            )

            match_pct = round(
                min(
                    100.0,
                    max(
                        0.0,
                        total_match,
                    ),
                ),
                1,
            )

            reasoning = self._build_reasoning(
                required_skills,
                skill_match,
                load_pct,
            )

            ranked.append(
                {
                    "member_id": member.get("id"),
                    "member_name": member.get("name"),
                    "role": member.get("role"),
                    "match_percentage": match_pct,
                    "current_load_pct": load_pct,
                    "reasoning": reasoning,
                }
            )

        ranked.sort(
            key=lambda item: (
                item["match_percentage"],
                item["member_name"] or "",
            ),
            reverse=True,
        )

        return ranked

    # ================================================================
    # Skill extraction
    # ================================================================

    @staticmethod
    def _extract_required_skills(
        task: Dict[str, Any],
    ) -> List[str]:

        skills = task.get(
            "required_skills"
        )

        if not skills:
            return []

        if isinstance(skills, dict):
            skills = list(
                skills.keys()
            )

        if isinstance(skills, str):
            skills = [
                value.strip()
                for value in skills.split(",")
                if value.strip()
            ]

        if not isinstance(skills, list):
            return []

        result = []

        for skill in skills:

            value = str(
                skill
            ).strip()

            if value and value not in result:
                result.append(value)

        return result

    # ================================================================
    # Member skill normalization
    # ================================================================

    @staticmethod
    def _normalize_skills(
        skills: Any,
    ) -> Dict[str, float]:

        if not isinstance(skills, dict):
            return {}

        normalized = {}

        for skill, value in skills.items():

            name = str(
                skill
            ).strip().lower()

            try:
                score = float(value)
            except (
                TypeError,
                ValueError,
            ):
                continue

            normalized[name] = max(
                0.0,
                min(
                    100.0,
                    score,
                ),
            )

        return normalized

    @staticmethod
    def _skill_match(
        member_skills: Dict[str, float],
        required_skill: str,
    ) -> float:
        """
        Match a required capability against member skills.

        Direct skill matches are preferred. Generic capability
        aliases allow concrete technologies to satisfy the
        corresponding architecture capability.

        No skill is fabricated when there is no evidence.
        """

        skill_name = str(
            required_skill
        ).strip().lower()

        # Direct match
        if skill_name in member_skills:
            return member_skills[skill_name]

        # Evidence-based technology/capability aliases.
        aliases = {
            "api development": [
                "fastapi",
                "flask",
                "django",
                "rest",
                "rest api",
                "restful api",
                "api",
            ],

            "relational database": [
                "sql",
                "postgresql",
                "postgres",
                "mysql",
                "mariadb",
                "oracle",
                "sqlite",
                "relational database",
            ],

            "authentication & authorization": [
                "authentication",
                "authorization",
                "oauth",
                "oauth2",
                "jwt",
                "identity",
                "access control",
            ],

            "notification systems": [
                "notification",
                "email",
                "messaging",
                "message queue",
                "push notifications",
            ],

            "api gateway": [
                "api gateway",
                "gateway",
                "reverse proxy",
                "nginx",
                "kong",
                "traefik",
            ],

            "search & filtering": [
                "search",
                "elasticsearch",
                "opensearch",
                "solr",
                "information retrieval",
            ],

            "payment processing": [
                "payment",
                "stripe",
                "razorpay",
                "paypal",
                "payment gateway",
            ],

            "reporting & analytics": [
                "analytics",
                "reporting",
                "data analytics",
                "power bi",
                "tableau",
            ],

            "file & document management": [
                "file management",
                "document management",
                "file upload",
                "document processing",
                "storage",
            ],
        }

        for alias in aliases.get(skill_name, []):
            if alias in member_skills:
                return member_skills[alias]

        return 0.0

    @staticmethod
    def _safe_percentage(
        value: Any,
    ) -> float:

        try:
            value = float(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0.0

        return max(
            0.0,
            min(
                100.0,
                value,
            ),
        )

    @staticmethod
    def _build_reasoning(
        required_skills: List[str],
        skill_match: float,
        load_pct: float,
    ) -> str:

        if required_skills:

            skills_text = ", ".join(
                required_skills
            )

            return (
                f"Required skills: {skills_text}. "
                f"Observed skill match is "
                f"{int(round(skill_match))}% "
                f"with current workload at "
                f"{int(round(load_pct))}%."
            )

        return (
            "No explicit technical skill evidence was "
            "provided for this task; ranking uses workload "
            "and availability without inventing required skills."
        )