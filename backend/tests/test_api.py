import pytest
import httpx

from backend.app.main import app
from backend.app.database import engine, Base, AsyncSessionLocal
from backend.app.services.seed_data import seed_initial_demo_data


async def ensure_db_ready():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_initial_demo_data(session)


@pytest.mark.asyncio
async def test_root_endpoint():
    await ensure_db_ready()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        res = await client.get("/")

        assert res.status_code == 200

        data = res.json()

        assert data["system"] == "ReqPilot AI"
        assert data["status"] == "online"


@pytest.mark.asyncio
async def test_projects_and_seeded_data():
    await ensure_db_ready()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:

        # ---------------------------------------------------------
        # 1. Fetch projects
        # ---------------------------------------------------------
        res = await client.get("/api/projects")

        assert res.status_code == 200

        projects = res.json()

        assert len(projects) >= 1

        # Explicitly select the reference project created by
        # seed_initial_demo_data() instead of assuming it is first.
        demo_project = next(
            (
                project
                for project in projects
                if project["title"]
                == "AI-Powered University Tutor Booking Platform"
            ),
            None,
        )

        assert demo_project is not None

        proj_id = demo_project["id"]

        # ---------------------------------------------------------
        # 2. Check project statistics
        # ---------------------------------------------------------
        stats_res = await client.get(
            f"/api/projects/{proj_id}/stats"
        )

        assert stats_res.status_code == 200

        stats = stats_res.json()

        assert stats["total_requirements"] > 0
        assert stats["health_score"] > 0

        # ---------------------------------------------------------
        # 3. Check requirements
        # ---------------------------------------------------------
        reqs_res = await client.get(
            f"/api/projects/{proj_id}/requirements"
        )

        assert reqs_res.status_code == 200

        reqs = reqs_res.json()

        assert len(reqs) >= 4

        # ---------------------------------------------------------
        # 4. Check issues
        # ---------------------------------------------------------
        issues_res = await client.get(
            f"/api/projects/{proj_id}/issues"
        )

        assert issues_res.status_code == 200

        assert isinstance(issues_res.json(), list)

        # ---------------------------------------------------------
        # 5. Check architecture
        # ---------------------------------------------------------
        arch_res = await client.get(
            f"/api/projects/{proj_id}/architecture"
        )

        assert arch_res.status_code == 200

        architecture = arch_res.json()

        assert len(architecture["modules"]) >= 5

        # ---------------------------------------------------------
        # 6. Check planning tasks
        # ---------------------------------------------------------
        tasks_res = await client.get(
            f"/api/projects/{proj_id}/tasks"
        )

        assert tasks_res.status_code == 200

        tasks = tasks_res.json()

        assert len(tasks) >= 3

        # ---------------------------------------------------------
        # 7. Check traceability matrix
        # ---------------------------------------------------------
        trace_res = await client.get(
            f"/api/projects/{proj_id}/traceability"
        )

        assert trace_res.status_code == 200

        traceability = trace_res.json()

        assert traceability["coverage_pct"] > 0

        # ---------------------------------------------------------
        # 8. Check evaluation endpoint
        # ---------------------------------------------------------
        # The evaluation endpoint runs against the reproducible
        # benchmark suite.
        eval_res = await client.get("/api/evaluation/run")

        assert eval_res.status_code == 200

        evaluation = eval_res.json()

        # ---------------------------------------------------------
        # Ambiguity benchmark
        # ---------------------------------------------------------
        # Current benchmark contains 2 ambiguity positive cases.
        assert evaluation["ambiguity_detection"]["total_samples"] == 2

        assert (
            evaluation["ambiguity_detection"]["f1_score"]
            == 1.0
        )

        # ---------------------------------------------------------
        # Conflict benchmark
        # ---------------------------------------------------------
        # Current benchmark contains 2 conflict positive cases.
        assert evaluation["conflict_detection"]["total_samples"] == 2

        assert (
            evaluation["conflict_detection"]["f1_score"]
            == 1.0
        )

        # ---------------------------------------------------------
        # Duplicate benchmark
        # ---------------------------------------------------------
        # Current benchmark contains 1 duplicate positive case.
        assert evaluation["duplicate_detection"]["total_samples"] == 1

        assert (
            evaluation["duplicate_detection"]["f1_score"]
            == 1.0
        )

        # ---------------------------------------------------------
        # Requirement extraction
        # ---------------------------------------------------------
        # There is currently no independently labeled extraction
        # ground truth in the benchmark.
        assert (
            evaluation["requirement_extraction"]["total_samples"]
            == 0
        )

        # ---------------------------------------------------------
        # Baseline comparison
        # ---------------------------------------------------------
        # No independently implemented baseline systems are
        # currently evaluated.
        assert evaluation["baseline_comparisons"] == []