import logging
from typing import List, Dict, Any

from backend.app.agents.llm_adapter import LLMAdapter
from backend.app.agents.ingestion_agent import IngestionAgent
from backend.app.agents.extraction_agent import ExtractionAgent
from backend.app.agents.quality_agent import QualityAgent
from backend.app.agents.ambiguity_agent import AmbiguityAgent
from backend.app.agents.conflict_agent import ConflictAgent
from backend.app.agents.duplicate_agent import DuplicateAgent
from backend.app.agents.clarification_agent import ClarificationAgent
from backend.app.agents.architecture_agent import ArchitectureAgent
from backend.app.agents.task_agent import TaskDecompositionAgent
from backend.app.agents.estimation_agent import EstimationAgent
from backend.app.agents.resource_agent import ResourceMatchingAgent
from backend.app.agents.scheduling_agent import SchedulingAgent
from backend.app.agents.traceability_agent import TraceabilityAgent
from backend.app.agents.change_impact_agent import ChangeImpactAgent
from backend.app.agents.report_agent import ReportGenerationAgent
from backend.app.agents.source_trust_verifier import SourceTrustVerifier


logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Coordinates the ReqPilot analysis pipeline.

    The pipeline is deterministic unless an agent explicitly uses
    the configured LLM adapter.

    Eight logical stages are reported consistently:

        1. Extraction
        2. Quality Analysis
        3. Issue Detection
        4. Clarifications
        5. Architecture
        6. Planning / Estimation
        7. Scheduling / Traceability
        8. Reports

    Change Impact is intentionally not executed during initial
    analysis because it requires a concrete change request.

    Source-Trust Verification is performed after traceability and
    before report generation. It is an automated source-alignment
    measure and does not claim ground-truth accuracy.
    """

    TOTAL_STEPS = 8

    def __init__(
        self,
        api_key: str = "",
        provider: str = "gemini",
        model: str = None,
    ):
        self.llm = LLMAdapter(
            api_key=api_key,
            provider=provider,
            model=model,
        )

        self.ingestion_agent = IngestionAgent()
        self.extraction_agent = ExtractionAgent(self.llm)
        self.quality_agent = QualityAgent()
        self.ambiguity_agent = AmbiguityAgent()
        self.conflict_agent = ConflictAgent(self.llm)
        self.duplicate_agent = DuplicateAgent()
        self.clarification_agent = ClarificationAgent()
        self.architecture_agent = ArchitectureAgent(self.llm)
        self.task_agent = TaskDecompositionAgent(self.llm)
        self.estimation_agent = EstimationAgent()
        self.resource_agent = ResourceMatchingAgent()
        self.scheduling_agent = SchedulingAgent()
        self.traceability_agent = TraceabilityAgent()
        self.change_impact_agent = ChangeImpactAgent()
        self.report_agent = ReportGenerationAgent()

        # ----------------------------------------------------------
        # Automated source-alignment / trust verification.
        #
        # This verifier checks the extracted requirements against the
        # original client document using:
        #   - evidence support
        #   - semantic alignment
        #   - constraint preservation
        #   - source coverage consistency
        #   - unsupported-content risk
        #
        # It does NOT claim conventional ground-truth accuracy.
        # ----------------------------------------------------------
        self.source_trust_verifier = SourceTrustVerifier()

    async def run_full_pipeline(
        self,
        project_data: Dict[str, Any],
        document_chunks: List[Dict[str, Any]],
        doc_filename: str = "Document.pdf",
    ) -> Dict[str, Any]:

        logs = []

        def log_step(message: str):
            logger.info(message)
            logs.append(message)

        # ----------------------------------------------------------
        # Validate source material
        # ----------------------------------------------------------

        if not document_chunks:
            raise ValueError(
                "No source document chunks were provided. "
                "Upload a requirements document before analysis."
            )

        log_step(
            f"Step 1/{self.TOTAL_STEPS}: "
            f"Initialized pipeline with "
            f"{len(document_chunks)} source chunks."
        )

        # ----------------------------------------------------------
        # 1. Requirement extraction
        # ----------------------------------------------------------

        log_step(
            f"Step 2/{self.TOTAL_STEPS}: "
            "Running Requirement Extraction Agent "
            "with evidence grounding..."
        )

        extracted_reqs = (
            await self.extraction_agent.extract_requirements(
                document_chunks,
                doc_filename,
            )
        )

        log_step(
            f"Extracted {len(extracted_reqs)} "
            "structured requirements."
        )

        if not extracted_reqs:
            raise ValueError(
                "Requirement extraction produced no requirements "
                "from the supplied source document."
            )

        # ----------------------------------------------------------
        # 2. Quality analysis
        # ----------------------------------------------------------

        log_step(
            f"Step 3/{self.TOTAL_STEPS}: "
            "Running Quality Agent across "
            "7 transparent dimensions..."
        )

        for req in extracted_reqs:

            quality_result = (
                self.quality_agent.evaluate_requirement(
                    req,
                    extracted_reqs,
                )
            )

            req["quality_score"] = (
                quality_result["quality_score"]
            )

            req["quality_breakdown"] = (
                quality_result["breakdown"]
            )

        # ----------------------------------------------------------
        # 3. Issues
        # ----------------------------------------------------------

        log_step(
            f"Step 4/{self.TOTAL_STEPS}: "
            "Detecting ambiguities, contradictions, "
            "and duplicates..."
        )

        ambiguities = (
            self.ambiguity_agent.detect_ambiguities(
                extracted_reqs
            )
        )

        conflicts = (
            await self.conflict_agent.detect_conflicts(
                extracted_reqs
            )
        )

        duplicates = (
            self.duplicate_agent.detect_duplicates(
                extracted_reqs
            )
        )

        all_issues = (
            ambiguities
            + conflicts
            + duplicates
        )

        log_step(
            f"Detected {len(ambiguities)} ambiguities, "
            f"{len(conflicts)} conflicts, "
            f"{len(duplicates)} duplicate candidates."
        )

        # ----------------------------------------------------------
        # 4. Clarifications
        # ----------------------------------------------------------

        clarifications = (
            self.clarification_agent
            .generate_clarification_questions(
                extracted_reqs,
                all_issues,
            )
        )

        log_step(
            f"Generated {len(clarifications)} "
            "prioritized stakeholder clarification questions."
        )

        # ----------------------------------------------------------
        # 5. Architecture
        # ----------------------------------------------------------

        log_step(
            f"Step 5/{self.TOTAL_STEPS}: "
            "Generating system architecture modules "
            "and interface topology..."
        )

        architecture_data = (
            self.architecture_agent.generate_architecture(
                extracted_reqs,
                project_data.get("title", ""),
            )
        )

        modules = architecture_data["modules"]
        relations = architecture_data["relations"]

        # Validate architecture IDs.
        architecture_module_ids = {
            module.get("id")
            for module in modules
            if module.get("id")
        }

        # ----------------------------------------------------------
        # 6. Task decomposition + estimation + resource matching
        # ----------------------------------------------------------

        log_step(
            f"Step 6/{self.TOTAL_STEPS}: "
            "Decomposing requirements into "
            "Epics, Features, and Tasks..."
        )

        task_data = (
            await self.task_agent.decompose_requirements(
                extracted_reqs,
                modules,
            )
        )

        epics = task_data["epics"]
        features = task_data["features"]
        tasks = task_data["tasks"]
        dependencies = task_data["dependencies"]

        # ----------------------------------------------------------
        # Validate task → architecture relationships.
        # ----------------------------------------------------------

        invalid_module_refs = []

        for task in tasks:

            module_id = task.get(
                "module_id"
            )

            if (
                module_id
                and module_id not in architecture_module_ids
            ):
                invalid_module_refs.append(
                    {
                        "task_id": task.get("id"),
                        "module_id": module_id,
                    }
                )

        if invalid_module_refs:

            logger.warning(
                "Tasks contain architecture module IDs "
                "not present in the generated architecture: %s",
                invalid_module_refs,
            )

            # Do not fabricate an architecture module.
            # Keep the task unassigned to architecture instead.
            for task in tasks:

                module_id = task.get(
                    "module_id"
                )

                if (
                    module_id
                    and module_id not in architecture_module_ids
                ):
                    task["module_id"] = None

        # ----------------------------------------------------------
        # Estimation
        # ----------------------------------------------------------

        log_step(
            "Running deterministic effort estimation "
            "for generated tasks..."
        )

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

            estimate = (
                self.estimation_agent.estimate_task(
                    task,
                    criteria_count,
                )
            )

            task["estimated_hours"] = (
                estimate["expected_hours"]
            )

            task["story_points"] = (
                estimate["story_points"]
            )

            task["estimate_min_hours"] = (
                estimate["min_hours"]
            )

            task["estimate_max_hours"] = (
                estimate["max_hours"]
            )

            task["estimate_confidence"] = (
                estimate["confidence_level"]
            )

        # ----------------------------------------------------------
        # Resource matching
        # ----------------------------------------------------------

        team_members = project_data.get(
            "team_members",
            [],
        )

        if team_members:

            log_step(
                "Running resource/skill matching "
                "against supplied team members..."
            )

            for task in tasks:

                candidates = (
                    self.resource_agent
                    .rank_candidates_for_task(
                        task,
                        team_members,
                    )
                )

                task["resource_candidates"] = candidates

                if candidates:
                    # Do not automatically assign a person.
                    # Preserve the ranked candidates for the UI
                    # and keep the task unassigned.
                    task["assignee_name"] = (
                        task.get(
                            "assignee_name",
                            "Unassigned",
                        )
                    )

        else:

            log_step(
                "No team members supplied; "
                "resource matching skipped without "
                "fabricating assignments."
            )

        # ----------------------------------------------------------
        # Scheduling
        # ----------------------------------------------------------

        schedule_result = (
            self.scheduling_agent.schedule_tasks(
                tasks,
                dependencies,
            )
        )

        tasks = schedule_result[
            "scheduled_tasks"
        ]

        sprints = schedule_result[
            "sprints"
        ]

        # ----------------------------------------------------------
        # 7. Traceability
        # ----------------------------------------------------------

        log_step(
            f"Step 7/{self.TOTAL_STEPS}: "
            "Constructing end-to-end traceability "
            "matrix and test cases..."
        )

        test_cases = (
            self.traceability_agent
            .generate_default_test_cases(
                extracted_reqs
            )
        )

        traceability_result = (
            self.traceability_agent
            .generate_traceability_matrix(
                extracted_reqs,
                tasks,
                test_cases,
                modules,
            )
        )

        # ----------------------------------------------------------
        # Source-Trust / Source-Alignment Verification
        #
        # This is performed after extraction and traceability so that
        # the verifier has the final requirement set while still
        # having access to the original document chunks.
        #
        # IMPORTANT:
        # This score is NOT conventional accuracy.
        # It is an automated source-alignment / trustworthiness
        # measure based on explicit verification checks.
        # ----------------------------------------------------------

        log_step(
            "Running automated Source-Trust Verification "
            "against the original client document..."
        )

        source_trust_result = (
            self.source_trust_verifier.verify(
                source_chunks=document_chunks,
                requirements=extracted_reqs,
            )
        )

        log_step(
            "Source-Trust Verification completed: "
            f"{source_trust_result['overall_score']:.2f}% "
            "source-alignment score."
        )

        # ----------------------------------------------------------
        # 8. Reports
        # ----------------------------------------------------------

        log_step(
            f"Step 8/{self.TOTAL_STEPS}: "
            "Generating analysis reports..."
        )

        srs_report = (
            self.report_agent.generate_srs(
                project_data,
                extracted_reqs,
            )
        )

        audit_report = (
            self.report_agent.generate_quality_audit(
                project_data,
                extracted_reqs,
                all_issues,
            )
        )

        architecture_report = (
            self.report_agent.generate_architecture_report(
                project_data,
                modules,
                relations,
            )
        )

        plan_report = (
            self.report_agent.generate_project_plan_report(
                project_data,
                tasks,
                sprints,
            )
        )

        traceability_report = (
            self.report_agent.generate_traceability_report(
                project_data,
                traceability_result["matrix"],
            )
        )

        reports = [
            {
                "report_type": "srs",
                "title": (
                    "Software Requirements Specification (SRS)"
                ),
                "content_markdown": srs_report,
            },
            {
                "report_type": "quality_audit",
                "title": (
                    "Requirements Quality & Risk Audit"
                ),
                "content_markdown": audit_report,
            },
            {
                "report_type": "architecture",
                "title": (
                    "System Architecture Proposal"
                ),
                "content_markdown": architecture_report,
            },
            {
                "report_type": "plan",
                "title": (
                    "Project Plan & Sprint Schedule"
                ),
                "content_markdown": plan_report,
            },
            {
                "report_type": "traceability",
                "title": (
                    "Traceability Matrix Report"
                ),
                "content_markdown": traceability_report,
            },
        ]

        log_step(
            "Pipeline execution successfully completed "
            "with evidence-grounded analysis."
        )

        return {
            "requirements": extracted_reqs,
            "issues": all_issues,
            "clarifications": clarifications,
            "modules": modules,
            "relations": relations,
            "epics": epics,
            "features": features,
            "tasks": tasks,
            "dependencies": dependencies,
            "sprints": sprints,
            "test_cases": test_cases,
            "traceability": traceability_result,

            # ------------------------------------------------------
            # NEW:
            # Automated source-alignment / trust verification result.
            # ------------------------------------------------------
            "source_trust": source_trust_result,

            "reports": reports,
            "logs": logs,
        }