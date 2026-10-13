import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_db
from backend.app.models import (
    Project,
    Requirement,
    RequirementIssue,
    ArchitectureModule,
    ArchitectureRelation,
    Task,
    Sprint,
    TestCase,
    ChangeRequest,
    ImpactItem,
    Report,
)
from backend.app.schemas import ReportResponse
from backend.app.agents.report_agent import ReportGenerationAgent
from backend.app.agents.traceability_agent import TraceabilityAgent


router = APIRouter(tags=["reports"])

report_agent = ReportGenerationAgent()
traceability_agent = TraceabilityAgent()


# ---------------------------------------------------------------------------
# GET ALL REPORTS
# ---------------------------------------------------------------------------

@router.get(
    "/api/projects/{project_id}/reports",
    response_model=List[ReportResponse],
)
async def list_reports(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return all persisted reports for a project.

    Reports are generated automatically only when none exist.
    """

    # Verify project exists first.
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalars().first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    result = await db.execute(
        select(Report)
        .where(Report.project_id == project_id)
        .order_by(Report.created_at)
    )

    reports = result.scalars().all()

    if not reports:
        await generate_all_reports(project_id, db)

        result = await db.execute(
            select(Report)
            .where(Report.project_id == project_id)
            .order_by(Report.created_at)
        )

        reports = result.scalars().all()

    return reports


# ---------------------------------------------------------------------------
# GET REPORT BY TYPE
# ---------------------------------------------------------------------------

@router.get(
    "/api/projects/{project_id}/reports/{report_type}",
    response_model=ReportResponse,
)
async def get_report_by_type(
    project_id: str,
    report_type: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return one persisted report by report type.

    If the requested report does not yet exist, the complete report set
    is generated from the project's persisted artifacts.
    """

    # Verify project exists.
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalars().first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    result = await db.execute(
        select(Report).where(
            Report.project_id == project_id,
            Report.report_type == report_type,
        )
    )

    report = result.scalars().first()

    if not report:
        await generate_all_reports(project_id, db)

        result = await db.execute(
            select(Report).where(
                Report.project_id == project_id,
                Report.report_type == report_type,
            )
        )

        report = result.scalars().first()

        if not report:
            raise HTTPException(
                status_code=404,
                detail=f"Report '{report_type}' not found",
            )

    return report


# ---------------------------------------------------------------------------
# GENERATE ALL REPORTS
# ---------------------------------------------------------------------------

@router.post("/api/projects/{project_id}/reports/generate")
async def generate_all_reports(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate the six engineering reports from persisted project artifacts.

    Reports:
        1. SRS
        2. Requirements Quality Audit
        3. Architecture Proposal
        4. Project Plan & Sprint Schedule
        5. Traceability Matrix
        6. Change Impact Report

    Important:
    - All data is project-scoped.
    - No synthetic project artifacts are created.
    - Existing sprint/task relationships are preserved.
    - Existing change-impact artifacts are loaded from the database.
    """

    # -----------------------------------------------------------------------
    # 1. LOAD PROJECT
    # -----------------------------------------------------------------------

    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )

    project = project_result.scalars().first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    project_data = {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "domain": project.domain,
        "status": project.status,
        "health_score": project.health_score,
    }

    # -----------------------------------------------------------------------
    # 2. LOAD REQUIREMENTS
    # -----------------------------------------------------------------------

    requirements_result = await db.execute(
        select(Requirement)
        .where(Requirement.project_id == project_id)
        .order_by(Requirement.created_at, Requirement.id)
    )

    requirement_rows = requirements_result.scalars().all()

    requirements = []

    for requirement in requirement_rows:
        requirements.append(
            {
                "id": requirement.id,
                "summary": requirement.summary,
                "description": requirement.description,
                "actor": requirement.actor,
                "action": requirement.action,
                "target_object": requirement.target_object,
                "preconditions": requirement.preconditions,
                "expected_outcome": requirement.expected_outcome,
                "acceptance_criteria": requirement.acceptance_criteria,
                "priority": requirement.priority,
                "status": requirement.status,
                "quality_score": requirement.quality_score,
                "quality_breakdown": requirement.quality_breakdown,
                "confidence": requirement.confidence,
                "source_id": requirement.source_id,
                "source_page": requirement.source_page,
                "source_excerpt": requirement.source_excerpt,
                "req_type": requirement.req_type,
                "version": requirement.version,
            }
        )

    # -----------------------------------------------------------------------
    # 3. LOAD REQUIREMENT ISSUES
    # -----------------------------------------------------------------------

    issues_result = await db.execute(
        select(RequirementIssue)
        .where(RequirementIssue.project_id == project_id)
        .order_by(RequirementIssue.created_at, RequirementIssue.id)
    )

    issue_rows = issues_result.scalars().all()

    issues = []

    for issue in issue_rows:
        issues.append(
            {
                "id": issue.id,
                "issue_type": issue.issue_type,
                "title": issue.title,
                "description": issue.description,
                "detected_phrase": issue.detected_phrase,
                "severity": issue.severity,
                "confidence": issue.confidence,
                "status": issue.status,
                "requirement_id": issue.requirement_id,
            }
        )

    # -----------------------------------------------------------------------
    # 4. LOAD ARCHITECTURE MODULES
    # -----------------------------------------------------------------------

    modules_result = await db.execute(
        select(ArchitectureModule)
        .where(ArchitectureModule.project_id == project_id)
        .order_by(ArchitectureModule.created_at, ArchitectureModule.id)
    )

    module_rows = modules_result.scalars().all()

    modules = []

    for module in module_rows:
        modules.append(
            {
                "id": module.id,
                "name": module.name,
                "description": module.description,
                "module_type": module.module_type,
                "tech_stack": module.tech_stack,
                "responsibilities": module.responsibilities,
                "api_endpoints": module.api_endpoints,
            }
        )

    # -----------------------------------------------------------------------
    # 5. LOAD ARCHITECTURE RELATIONS
    # -----------------------------------------------------------------------

    relations_result = await db.execute(
        select(ArchitectureRelation)
        .where(ArchitectureRelation.project_id == project_id)
        .order_by(
            ArchitectureRelation.created_at,
            ArchitectureRelation.id,
        )
    )

    relation_rows = relations_result.scalars().all()

    relations = []

    for relation in relation_rows:
        relations.append(
            {
                "source_module_id": relation.source_module_id,
                "target_module_id": relation.target_module_id,
                "relation_type": relation.relation_type,
                "description": relation.description,
            }
        )

    # -----------------------------------------------------------------------
    # 6. LOAD TASKS
    # -----------------------------------------------------------------------

    task_result = await db.execute(
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.created_at, Task.id)
    )

    task_rows = task_result.scalars().all()

    tasks = []

    for task in task_rows:
        tasks.append(
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "requirement_id": task.requirement_id,
                "module_id": task.module_id,
                "epic_id": task.epic_id,
                "feature_id": task.feature_id,
                "complexity": task.complexity,
                "estimated_hours": task.estimated_hours,
                "story_points": task.story_points,
                "priority": task.priority,
                "status": task.status,
                "assignee_name": task.assignee_name,
                "sprint_name": task.sprint_name,
                "subtasks": task.subtasks,
                "acceptance_criteria": task.acceptance_criteria,
            }
        )

    # -----------------------------------------------------------------------
    # 7. LOAD TEST CASES
    # -----------------------------------------------------------------------

    test_result = await db.execute(
        select(TestCase)
        .where(TestCase.project_id == project_id)
        .order_by(TestCase.id)
    )

    test_rows = test_result.scalars().all()

    tests = []

    for test_case in test_rows:
        tests.append(
            {
                "id": test_case.id,
                "title": test_case.title,
                "test_type": test_case.test_type,
                "requirement_id": test_case.requirement_id,
                "task_id": test_case.task_id,
                "preconditions": test_case.preconditions,
                "steps": test_case.steps,
                "expected_result": test_case.expected_result,
                "status": test_case.status,
            }
        )

    # -----------------------------------------------------------------------
    # 8. LOAD SPRINTS
    # -----------------------------------------------------------------------

    sprint_result = await db.execute(
        select(Sprint)
        .where(Sprint.project_id == project_id)
        .order_by(Sprint.start_date, Sprint.name)
    )

    sprint_rows = sprint_result.scalars().all()

    sprints = []

    for sprint in sprint_rows:
        sprint_task_ids = [
            task["id"]
            for task in tasks
            if task.get("sprint_name") == sprint.name
        ]

        sprints.append(
            {
                "sprint_name": sprint.name,
                "goal": sprint.goal,
                "start_date": sprint.start_date,
                "end_date": sprint.end_date,
                "total_points": sprint.capacity_points,
                "task_ids": sprint_task_ids,
                "status": sprint.status,
            }
        )

    # IMPORTANT:
    # Do not fabricate a Sprint 1 if there are no persisted sprints.
    # The report agent will receive an empty list and can truthfully
    # report that no sprint schedule is persisted.

    # -----------------------------------------------------------------------
    # 9. LOAD CHANGE REQUESTS
    # -----------------------------------------------------------------------

    change_request_result = await db.execute(
        select(ChangeRequest)
        .where(ChangeRequest.project_id == project_id)
        .order_by(
            ChangeRequest.created_at,
            ChangeRequest.id,
        )
    )

    change_request_rows = change_request_result.scalars().all()

    # -----------------------------------------------------------------------
    # 10. LOAD ACTUAL CHANGE IMPACT ITEMS
    # -----------------------------------------------------------------------

    impact_result = await db.execute(
        select(ImpactItem)
        .join(
            ChangeRequest,
            ImpactItem.change_request_id == ChangeRequest.id,
        )
        .where(ChangeRequest.project_id == project_id)
        .order_by(
            ImpactItem.change_request_id,
            ImpactItem.artifact_type,
            ImpactItem.artifact_id,
        )
    )

    impact_rows = impact_result.scalars().all()

    impact_items_by_change_request = {}

    for impact_item in impact_rows:
        impact_items_by_change_request.setdefault(
            impact_item.change_request_id,
            [],
        ).append(
            {
                "artifact_type": impact_item.artifact_type,
                "artifact_id": impact_item.artifact_id,
                "artifact_name": impact_item.artifact_name,
                "impact_description": impact_item.impact_description,
                "severity": impact_item.severity,
            }
        )

    crs = []

    for change_request in change_request_rows:
        crs.append(
            {
                "id": change_request.id,
                "title": change_request.title,
                "description": change_request.description,
                "requirement_id": change_request.requirement_id,
                "risk_level": change_request.risk_level,
                "schedule_impact": change_request.schedule_impact,
                "status": change_request.status,
                "proposed_summary": change_request.proposed_summary,
                "proposed_description": change_request.proposed_description,
                "impact_items": impact_items_by_change_request.get(
                    change_request.id,
                    [],
                ),
            }
        )

    # -----------------------------------------------------------------------
    # 11. GENERATE TRACEABILITY MATRIX FROM REAL ARTIFACTS
    # -----------------------------------------------------------------------

    traceability_result = (
        traceability_agent.generate_traceability_matrix(
            requirements,
            tasks,
            tests,
            modules,
        )
    )

    traceability_matrix = traceability_result.get("matrix", [])

    # -----------------------------------------------------------------------
    # 12. GENERATE SIX REPORTS
    # -----------------------------------------------------------------------

    srs_markdown = report_agent.generate_srs(
        project_data,
        requirements,
    )

    quality_audit_markdown = report_agent.generate_quality_audit(
        project_data,
        requirements,
        issues,
    )

    architecture_markdown = report_agent.generate_architecture_report(
        project_data,
        modules,
        relations,
    )

    project_plan_markdown = report_agent.generate_project_plan_report(
        project_data,
        tasks,
        sprints,
    )

    traceability_markdown = report_agent.generate_traceability_report(
        project_data,
        traceability_matrix,
    )

    change_impact_markdown = report_agent.generate_change_impact_report(
        project_data,
        crs,
    )

    # -----------------------------------------------------------------------
    # 13. REPLACE CURRENT REPORT SNAPSHOT
    # -----------------------------------------------------------------------

    await db.execute(
        delete(Report).where(
            Report.project_id == project_id
        )
    )

    generated_at = datetime.utcnow()

    reports_to_add = [
        Report(
            id=str(uuid.uuid4()),
            project_id=project_id,
            report_type="srs",
            title="Software Requirements Specification (SRS)",
            content_markdown=srs_markdown,
            created_at=generated_at,
        ),
        Report(
            id=str(uuid.uuid4()),
            project_id=project_id,
            report_type="quality_audit",
            title="Requirements Quality & Risk Audit",
            content_markdown=quality_audit_markdown,
            created_at=generated_at,
        ),
        Report(
            id=str(uuid.uuid4()),
            project_id=project_id,
            report_type="architecture",
            title="System Architecture Proposal",
            content_markdown=architecture_markdown,
            created_at=generated_at,
        ),
        Report(
            id=str(uuid.uuid4()),
            project_id=project_id,
            report_type="plan",
            title="Project Plan & Sprint Schedule",
            content_markdown=project_plan_markdown,
            created_at=generated_at,
        ),
        Report(
            id=str(uuid.uuid4()),
            project_id=project_id,
            report_type="traceability",
            title="Traceability Matrix Report",
            content_markdown=traceability_markdown,
            created_at=generated_at,
        ),
        Report(
            id=str(uuid.uuid4()),
            project_id=project_id,
            report_type="change_impact",
            title="Requirements Change Impact Report",
            content_markdown=change_impact_markdown,
            created_at=generated_at,
        ),
    ]

    db.add_all(reports_to_add)

    await db.commit()

    return {
        "message": "All 6 engineering reports successfully generated",
        "count": len(reports_to_add),
        "project_id": project_id,
        "report_types": [
            "srs",
            "quality_audit",
            "architecture",
            "plan",
            "traceability",
            "change_impact",
        ],
    }