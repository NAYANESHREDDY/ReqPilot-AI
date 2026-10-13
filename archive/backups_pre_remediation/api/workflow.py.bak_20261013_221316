import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models import (
    Project,
    DocumentChunk,
    Requirement,
    RequirementIssue,
    ClarificationQuestion,
    ArchitectureModule,
    ArchitectureRelation,
    Epic,
    Feature,
    Task,
    TaskDependency,
    Sprint,
    TestCase,
    TraceabilityLink,
    Report,
    TeamMember,
    AIWorkflow,
)
from backend.app.schemas import AnalyzeRequest, WorkflowStatusResponse
from backend.app.agents.orchestrator import WorkflowOrchestrator
from backend.app.config import settings


router = APIRouter(tags=["workflow"])


def make_project_scoped_id(project_id: str, logical_id: str) -> str:
    """
    Convert an agent-generated logical ID into a globally unique,
    project-scoped database ID.

    Example:
        FR-001 -> 05DEE9BF-FR-001
        MOD-AUTH -> 05DEE9BF-MOD-AUTH
        EPIC-01 -> 05DEE9BF-EPIC-01

    The prefix is derived from the project's UUID and is short enough
    to remain safely within the existing VARCHAR(50) database columns.
    """
    if not logical_id:
        return str(uuid.uuid4())

    project_prefix = project_id.replace("-", "")[:8].upper()
    return f"{project_prefix}-{logical_id}"


def build_id_map(project_id: str, items, key: str = "id") -> dict:
    """
    Build a mapping from agent logical IDs to project-scoped DB IDs.
    """
    result = {}

    for item in items:
        logical_id = item.get(key)

        if logical_id:
            result[logical_id] = make_project_scoped_id(
                project_id,
                logical_id,
            )

    return result


@router.post("/api/projects/{project_id}/analyze")
async def trigger_analysis(
    project_id: str,
    req_body: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    # ------------------------------------------------------------------
    # 1. Fetch project
    # ------------------------------------------------------------------
    p_res = await db.execute(
        select(Project).where(Project.id == project_id)
    )

    project = p_res.scalars().first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # ------------------------------------------------------------------
    # 2. Fetch uploaded document chunks
    # ------------------------------------------------------------------
    c_res = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.project_id == project_id)
        .order_by(DocumentChunk.chunk_index)
    )

    chunks = c_res.scalars().all()

    # ------------------------------------------------------------------
    # 3. Prepare source data
    # ------------------------------------------------------------------
    chunk_dicts = []
    doc_filename = "Project_Scope.txt"

    if chunks:
        # Use the actual uploaded chunks.
        #
        # We do not invent document content when uploaded source
        # material exists.
        doc_filename = "Uploaded_Specification"

        chunk_dicts = [
            {
                "chunk_index": c.chunk_index,
                "section_title": c.section_title,
                "page_number": c.page_number,
                "content": c.content,
                "token_count": c.token_count,
            }
            for c in chunks
        ]

    else:
        # Preserve the existing fallback behavior for projects that
        # have no uploaded document, but make the synthetic nature
        # explicit in the filename/logging.
        raise HTTPException(
        status_code=400,
        detail="No processed document chunks found for this project. Upload and process a source document before analysis."
    )

    # ------------------------------------------------------------------
    # 4. Create workflow record
    # ------------------------------------------------------------------
    wf_id = str(uuid.uuid4())

    workflow = AIWorkflow(
        id=wf_id,
        project_id=project_id,
        workflow_type="full_pipeline",
        status="running",
        current_step="Executing Multi-Agent Orchestrator",
        current_step_index=1,
        total_steps=WorkflowOrchestrator.TOTAL_STEPS,
        progress_pct=12.5,
        log_messages=[
            "Started multi-agent requirements analysis."
        ],
        created_at=datetime.utcnow(),
    )

    db.add(workflow)

    await db.flush()

    # ------------------------------------------------------------------
    # 5. Determine LLM configuration
    # ------------------------------------------------------------------
    provider = req_body.provider or "gemini"

    default_keys = {
        "gemini": settings.GEMINI_API_KEY,
        "openai": settings.OPENAI_API_KEY,
        "groq": settings.GROQ_API_KEYS or settings.GROQ_API_KEY,
    }

    api_key = req_body.api_key or default_keys.get(provider, "")

    model = req_body.model

    if not model and provider == "groq":
        model = settings.GROQ_MODEL

    orchestrator = WorkflowOrchestrator(
        api_key=api_key if req_body.use_llm else "",
        provider=provider,
        model=model,
    )

    # ------------------------------------------------------------------
    # 6. Prepare project dictionary
    # ------------------------------------------------------------------
    
    team_result = await db.execute(
    select(TeamMember).where(
        TeamMember.project_id == project_id
    )
    )

    team_members = team_result.scalars().all()

    proj_dict = {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "domain": project.domain,
        "team_members": [
            {
                "id": member.id,
                "name": member.name,
                "email": member.email,
                "role": member.role,
                "capacity_hours_per_week": member.capacity_hours_per_week,
                "current_load_pct": member.current_load_pct,
                "skills": member.skills,
            }
            for member in team_members
        ],
    }

    # ------------------------------------------------------------------
    # 7. Execute multi-agent pipeline
    # ------------------------------------------------------------------
    try:
        pipeline_result = await orchestrator.run_full_pipeline(
            proj_dict,
            chunk_dicts,
            doc_filename,
        )

    except Exception as exc:
        # Never leave a workflow falsely marked as successful.
        workflow.status = "failed"
        workflow.current_step = "Analysis Failed"
        workflow.progress_pct = 0.0
        workflow.log_messages = [
            "Multi-agent analysis failed.",
            str(exc),
        ]

        await db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}",
        ) from exc

    # ------------------------------------------------------------------
    # 8. Clean old generated data for this project only
    # ------------------------------------------------------------------
    #
    # IMPORTANT:
    # These deletes are restricted by project_id.
    # Existing data belonging to another project is untouched.
    #

    await db.execute(
        delete(RequirementIssue).where(
            RequirementIssue.project_id == project_id
        )
    )

    await db.execute(
        delete(ClarificationQuestion).where(
            ClarificationQuestion.project_id == project_id
        )
    )

    await db.execute(
        delete(ArchitectureRelation).where(
            ArchitectureRelation.project_id == project_id
        )
    )

    await db.execute(
        delete(ArchitectureModule).where(
            ArchitectureModule.project_id == project_id
        )
    )
    await db.execute(
    delete(Sprint).where(
        Sprint.project_id == project_id
    )
    )

    await db.execute(
        delete(TraceabilityLink).where(
            TraceabilityLink.project_id == project_id
        )
    )

    # Delete dependencies before tasks.
    await db.execute(
        delete(TaskDependency).where(
            TaskDependency.task_id.in_(
                select(Task.id).where(
                    Task.project_id == project_id
                )
            )
        )
    )

    await db.execute(
        delete(Task).where(
            Task.project_id == project_id
        )
    )

    await db.execute(
        delete(Feature).where(
            Feature.project_id == project_id
        )
    )

    await db.execute(
        delete(Epic).where(
            Epic.project_id == project_id
        )
    )

    await db.execute(
        delete(TestCase).where(
            TestCase.project_id == project_id
        )
    )

    await db.execute(
        delete(Report).where(
            Report.project_id == project_id
        )
    )

    await db.execute(
        delete(Requirement).where(
            Requirement.project_id == project_id
        )
    )

    # ------------------------------------------------------------------
    # 9. Extract pipeline collections
    # ------------------------------------------------------------------
    requirements = pipeline_result.get("requirements", [])
    issues = pipeline_result.get("issues", [])
    clarifications = pipeline_result.get("clarifications", [])
    modules = pipeline_result.get("modules", [])
    relations = pipeline_result.get("relations", [])
    epics = pipeline_result.get("epics", [])
    features = pipeline_result.get("features", [])
    tasks = pipeline_result.get("tasks", [])
    dependencies = pipeline_result.get("dependencies", [])
    sprints = pipeline_result.get("sprints", [])
    test_cases = pipeline_result.get("test_cases", [])
    traceability = pipeline_result.get("traceability", {})
    traceability_matrix = traceability.get("matrix", [])
    reports = pipeline_result.get("reports", [])

    # ------------------------------------------------------------------
    # 10. Build all ID mappings
    # ------------------------------------------------------------------
    #
    # Agents continue using their normal logical IDs:
    #
    # FR-001
    # MOD-AUTH
    # EPIC-01
    # FEAT-01
    # TASK-001
    # TEST-001
    #
    # Database receives project-scoped IDs.
    #

    requirement_id_map = build_id_map(
        project_id,
        requirements,
    )

    module_id_map = build_id_map(
        project_id,
        modules,
    )

    epic_id_map = build_id_map(
        project_id,
        epics,
    )

    feature_id_map = build_id_map(
        project_id,
        features,
    )

    task_id_map = build_id_map(
        project_id,
        tasks,
    )

    test_id_map = build_id_map(
        project_id,
        test_cases,
    )

    # ------------------------------------------------------------------
    # 11. Persist Requirements
    # ------------------------------------------------------------------
    req_objs = []

    for r in requirements:
        logical_id = r["id"]

        db_requirement_id = requirement_id_map.get(
            logical_id,
            make_project_scoped_id(project_id, logical_id),
        )

        req_objs.append(
            Requirement(
                id=db_requirement_id,
                project_id=project_id,
                req_type=r["req_type"],
                summary=r["summary"],
                description=r["description"],
                actor=r["actor"],
                action=r["action"],
                target_object=r["target_object"],
                preconditions=r.get("preconditions", ""),
                expected_outcome=r.get("expected_outcome", ""),
                acceptance_criteria=r.get(
                    "acceptance_criteria",
                    [],
                ),
                priority=r.get(
                    "priority",
                    "medium",
                ),
                status=r.get(
                    "status",
                    "needs_review",
                ),
                quality_score=r.get(
                    "quality_score",
                    80.0,
                ),
                quality_breakdown=r.get(
                    "quality_breakdown",
                    {},
                ),
                confidence=r.get(
                    "confidence",
                    0.90,
                ),
                is_ai_suggested=r.get(
                    "is_ai_suggested",
                    False,
                ),
                version=1,
                source_id=r.get(
                    "source_id"
                ),
                source_page=r.get(
                    "source_page"
                ),
                source_excerpt=r.get(
                    "source_excerpt",
                    "",
                ),
            )
        )

    db.add_all(req_objs)

    # ------------------------------------------------------------------
    # 12. Persist Issues
    # ------------------------------------------------------------------
    issue_objs = []

    for iss in issues:
        logical_requirement_id = iss.get(
            "requirement_id"
        )

        logical_conflict_id = iss.get(
            "conflict_with_id"
        )

        issue_objs.append(
            RequirementIssue(
                id=str(uuid.uuid4()),
                project_id=project_id,

                requirement_id=(
                    requirement_id_map.get(
                        logical_requirement_id
                    )
                    if logical_requirement_id
                    else None
                ),

                conflict_with_id=(
                    requirement_id_map.get(
                        logical_conflict_id
                    )
                    if logical_conflict_id
                    else None
                ),

                issue_type=iss["issue_type"],
                title=iss["title"],
                description=iss["description"],
                detected_phrase=iss.get(
                    "detected_phrase",
                    "",
                ),
                severity=iss.get(
                    "severity",
                    "medium",
                ),
                confidence=iss.get(
                    "confidence",
                    0.85,
                ),
                status="open",
            )
        )

    db.add_all(issue_objs)

    # ------------------------------------------------------------------
    # 13. Persist Clarifications
    # ------------------------------------------------------------------
    clarif_objs = []

    for q in clarifications:
        logical_requirement_id = q.get(
            "requirement_id"
        )

        clarif_objs.append(
            ClarificationQuestion(
                id=str(uuid.uuid4()),
                project_id=project_id,

                requirement_id=(
                    requirement_id_map.get(
                        logical_requirement_id
                    )
                    if logical_requirement_id
                    else None
                ),

                question=q["question"],
                rationale=q.get(
                    "rationale",
                    "",
                ),
                priority=q.get(
                    "priority",
                    "medium",
                ),
                suggested_options=q.get(
                    "suggested_options",
                    [],
                ),
                status="pending",
            )
        )

    db.add_all(clarif_objs)

    # ------------------------------------------------------------------
    # 14. Persist Architecture Modules
    # ------------------------------------------------------------------
    mod_objs = []

    for m in modules:
        logical_module_id = m["id"]

        db_module_id = module_id_map.get(
            logical_module_id,
            make_project_scoped_id(
                project_id,
                logical_module_id,
            ),
        )

        mod_objs.append(
            ArchitectureModule(
                id=db_module_id,
                project_id=project_id,
                name=m["name"],
                description=m.get(
                    "description",
                    "",
                ),
                module_type=m.get(
                    "module_type",
                    "service",
                ),
                tech_stack=m.get(
                    "tech_stack",
                    "",
                ),
                responsibilities=m.get(
                    "responsibilities",
                    [],
                ),
                api_endpoints=m.get(
                    "api_endpoints",
                    [],
                ),
                pos_x=m.get(
                    "pos_x",
                    100.0,
                ),
                pos_y=m.get(
                    "pos_y",
                    100.0,
                ),
                is_ai_suggested=m.get(
                    "is_ai_suggested",
                    True,
                ),
                status=m.get(
                    "status",
                    "approved",
                ),
            )
        )

    db.add_all(mod_objs)

    await db.flush()

    # ------------------------------------------------------------------
    # 15. Persist Architecture Relations
    # ------------------------------------------------------------------
    rel_objs = []

    for rel in relations:
        logical_source = rel.get(
            "source_module_id"
        )

        logical_target = rel.get(
            "target_module_id"
        )

        mapped_source = module_id_map.get(
            logical_source
        )

        mapped_target = module_id_map.get(
            logical_target
        )

        # Do not create a relation to a nonexistent module.
        if not mapped_source or not mapped_target:
            continue

        rel_objs.append(
            ArchitectureRelation(
                id=str(uuid.uuid4()),
                project_id=project_id,
                source_module_id=mapped_source,
                target_module_id=mapped_target,
                relation_type=rel.get(
                    "relation_type",
                    "calls",
                ),
                description=rel.get(
                    "description",
                    "",
                ),
            )
        )

    db.add_all(rel_objs)

    # ------------------------------------------------------------------
    # 16. Persist Epics
    # ------------------------------------------------------------------
    for epic in epics:
        logical_epic_id = epic["id"]

        db_epic_id = epic_id_map.get(
            logical_epic_id,
            make_project_scoped_id(
                project_id,
                logical_epic_id,
            ),
        )

        db.add(
            Epic(
                id=db_epic_id,
                project_id=project_id,
                title=epic["title"],
                description=epic.get(
                    "description",
                    "",
                ),
                status=epic.get(
                    "status",
                    "in_progress",
                ),
            )
        )

    await db.flush()

    # ------------------------------------------------------------------
    # 17. Persist Features
    # ------------------------------------------------------------------
    for feat in features:
        logical_feature_id = feat["id"]
        logical_epic_id = feat.get(
            "epic_id"
        )

        db_feature_id = feature_id_map.get(
            logical_feature_id,
            make_project_scoped_id(
                project_id,
                logical_feature_id,
            ),
        )

        db_epic_id = epic_id_map.get(
            logical_epic_id
        )

        # Never create a feature pointing at an unknown epic.
        if not db_epic_id:
            continue

        db.add(
            Feature(
                id=db_feature_id,
                epic_id=db_epic_id,
                project_id=project_id,
                title=feat["title"],
                description=feat.get(
                    "description",
                    "",
                ),
            )
        )

    await db.flush()

    # ------------------------------------------------------------------
    # 18. Persist Tasks
    # ------------------------------------------------------------------
    for t in tasks:
        logical_task_id = t["id"]

        logical_epic_id = t.get(
            "epic_id"
        )

        logical_feature_id = t.get(
            "feature_id"
        )

        logical_requirement_id = t.get(
            "requirement_id"
        )

        logical_module_id = t.get(
            "module_id"
        )

        db_task_id = task_id_map.get(
            logical_task_id,
            make_project_scoped_id(
                project_id,
                logical_task_id,
            ),
        )

        db_epic_id = (
            epic_id_map.get(
                logical_epic_id
            )
            if logical_epic_id
            else None
        )

        db_feature_id = (
            feature_id_map.get(
                logical_feature_id
            )
            if logical_feature_id
            else None
        )

        db_requirement_id = (
            requirement_id_map.get(
                logical_requirement_id
            )
            if logical_requirement_id
            else None
        )

        db_module_id = (
            module_id_map.get(
                logical_module_id
            )
            if logical_module_id
            else None
        )

        db.add(
            Task(
                id=db_task_id,
                project_id=project_id,
                epic_id=db_epic_id,
                feature_id=db_feature_id,
                requirement_id=db_requirement_id,
                module_id=db_module_id,
                title=t["title"],
                description=t.get(
                    "description",
                    "",
                ),
                complexity=t.get(
                    "complexity",
                    "medium",
                ),
                estimated_hours=t.get(
                    "estimated_hours",
                    8.0,
                ),
                story_points=t.get(
                    "story_points",
                    3,
                ),
                priority=t.get(
                    "priority",
                    "medium",
                ),
                status="todo",
                assignee_name=t.get(
                    "assignee_name",
                    "Unassigned",
                ),
                sprint_name=t.get(
                    "sprint_name",
                    "Sprint 1",
                ),
                subtasks=t.get(
                    "subtasks",
                    [],
                ),
                acceptance_criteria=t.get(
                    "acceptance_criteria",
                    [],
                ),
            )
        )

    await db.flush()
    # ------------------------------------------------------------------
# 19. Persist Sprints
# ------------------------------------------------------------------

    for sprint in sprints:
        sprint_name = sprint.get("sprint_name")

        if not sprint_name:
            continue

        db.add(
            Sprint(
                id=str(uuid.uuid4()),
                project_id=project_id,
                name=sprint_name,
                goal=None,
                start_date=None,
                end_date=None,
                capacity_points=25,
                status="planned",
            )
        )

    await db.flush()

    # ------------------------------------------------------------------
    # 19. Persist Task Dependencies
    # ------------------------------------------------------------------
    for dep in dependencies:
        logical_task_id = dep.get(
            "task_id"
        )

        logical_parent_task_id = dep.get(
            "depends_on_task_id"
        )

        db_task_id = task_id_map.get(
            logical_task_id
        )

        db_parent_task_id = task_id_map.get(
            logical_parent_task_id
        )

        # Never create dangling dependencies.
        if not db_task_id or not db_parent_task_id:
            continue

        db.add(
            TaskDependency(
                id=str(uuid.uuid4()),
                task_id=db_task_id,
                depends_on_task_id=db_parent_task_id,
                dependency_type=dep.get(
                    "dependency_type",
                    "blocks",
                ),
            )
        )

    await db.flush()

    # ------------------------------------------------------------------
    # 20. Persist Test Cases
    # ------------------------------------------------------------------
    #
    # Generated tests describe tests that should be executed later.
    # They are therefore NEVER marked as passed here.
    #
    for tc in test_cases:
        logical_test_id = tc["id"]

        logical_requirement_id = tc.get(
            "requirement_id"
        )

        db_test_id = test_id_map.get(
            logical_test_id,
            make_project_scoped_id(
                project_id,
                logical_test_id,
            ),
        )

        db_requirement_id = (
            requirement_id_map.get(
                logical_requirement_id
            )
            if logical_requirement_id
            else None
        )

        if not db_requirement_id:
            continue

        db.add(
            TestCase(
                id=db_test_id,
                project_id=project_id,
                requirement_id=db_requirement_id,
                title=tc["title"],
                test_type=tc.get(
                    "test_type",
                    "integration",
                ),
                preconditions=tc.get(
                    "preconditions",
                    "",
                ),
                steps=tc.get(
                    "steps",
                    [],
                ),
                expected_result=tc.get(
                    "expected_result",
                    "",
                ),
                status="not_run",
            )
        )

    await db.flush()

    # ------------------------------------------------------------------
# Persist Traceability Links
# ------------------------------------------------------------------

    for entry in traceability_matrix:
        logical_requirement_id = entry.get("requirement_id")

        db_requirement_id = requirement_id_map.get(
            logical_requirement_id
        )

        if not db_requirement_id:
            continue

        logical_module_id = entry.get("module_id")

        db_module_id = (
            module_id_map.get(logical_module_id)
            if logical_module_id
            else None
        )

        source_id = entry.get("source_id")

        logical_task_ids = entry.get("task_ids", [])
        logical_test_ids = entry.get("test_ids", [])

        for logical_task_id in logical_task_ids:
            db_task_id = task_id_map.get(logical_task_id)

            if not db_task_id:
                continue

            db.add(
                TraceabilityLink(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    source_id=source_id,
                    requirement_id=db_requirement_id,
                    module_id=db_module_id,
                    task_id=db_task_id,
                    test_id=None,
                    status="linked",
                )
            )

        for logical_test_id in logical_test_ids:
            db_test_id = test_id_map.get(logical_test_id)

            if not db_test_id:
                continue

            db.add(
                TraceabilityLink(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    source_id=source_id,
                    requirement_id=db_requirement_id,
                    module_id=db_module_id,
                    task_id=None,
                    test_id=db_test_id,
                    status="linked",
                )
            )

    await db.flush()

    # ------------------------------------------------------------------
    # 21. Persist Reports
    # ------------------------------------------------------------------
    for rep in reports:
        db.add(
            Report(
                id=str(uuid.uuid4()),
                project_id=project_id,
                report_type=rep["report_type"],
                title=rep["title"],
                content_markdown=rep[
                    "content_markdown"
                ],
                content_json=rep.get(
                    "content_json"
                ),
                created_at=datetime.utcnow(),
            )
        )

    # ------------------------------------------------------------------
    # 22. Complete workflow
    # ------------------------------------------------------------------
    workflow.status = "completed"
    workflow.progress_pct = 100.0
    workflow.current_step = "Analysis Complete"
    workflow.current_step_index = WorkflowOrchestrator.TOTAL_STEPS
    workflow.log_messages = pipeline_result.get(
        "logs",
        [],
    )
    workflow.completed_at = datetime.utcnow()

    await db.commit()

    # ------------------------------------------------------------------
    # 23. Return result
    # ------------------------------------------------------------------
    return {
        "status": "success",
        "workflow_id": wf_id,
        "extracted_requirements": len(requirements),
        "detected_issues": len(issues),
        "generated_modules": len(modules),
        "generated_tasks": len(tasks),
        "generated_reports": len(reports),
        "logs": pipeline_result.get(
            "logs",
            [],
        ),
    }


@router.get(
    "/api/workflows/{id}",
    response_model=WorkflowStatusResponse,
)
async def get_workflow_status(
    id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AIWorkflow).where(
            AIWorkflow.id == id
        )
    )

    wf = result.scalars().first()

    if not wf:
        raise HTTPException(
            status_code=404,
            detail="Workflow not found",
        )

    return {
        "id": wf.id,
        "project_id": wf.project_id,
        "status": wf.status,
        "current_step": wf.current_step,
        "current_step_index": wf.current_step_index,
        "total_steps": wf.total_steps,
        "progress_pct": wf.progress_pct,
        "log_messages": wf.log_messages or [],
    }