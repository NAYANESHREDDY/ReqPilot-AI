import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import (
    User, Project, Document, DocumentChunk, Requirement, RequirementIssue,
    ClarificationQuestion, ArchitectureModule, ArchitectureRelation, Epic, Feature,
    Task, TeamMember, TestCase, ChangeRequest, ImpactItem, Report, Sprint
)

async def seed_initial_demo_data(db: AsyncSession):
    """Seed the reference project: AI-Powered University Tutor Booking Platform (Section 45)."""
    # Check if data already exists
    res = await db.execute(select(Project).where(Project.title.like("%Tutor Booking%")))
    if res.scalars().first():
        return

    # 1. Create Demo User
    demo_user = User(
        id=str(uuid.uuid4()),
        email="lead.analyst@reqpilot.ai",
        full_name="Alex Mercer (Lead Requirements Engineer)",
        hashed_password="demo_hashed_password",
        role="admin",
        created_at=datetime.utcnow(),
    )
    db.add(demo_user)

    # 2. Create Reference Project
    project = Project(
        id=str(uuid.uuid4()),
        title="AI-Powered University Tutor Booking Platform",
        description="A comprehensive peer tutoring platform enabling university students to search verified tutors, reserve 1-on-1 sessions, execute secure escrow payments, and receive real-time schedule notifications with admin telemetry.",
        domain="EdTech / Marketplace",
        status="active",
        health_score=94.5,
        created_by=demo_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(project)
    await db.flush()

    # 3. Source Document
    doc = Document(
        id=str(uuid.uuid4()),
        project_id=project.id,
        filename="Tutor_Booking_Platform_RFP_Specification.pdf",
        file_type="pdf",
        file_size=1048576,
        storage_path="uploads/tutor_booking_rfp.pdf",
        status="processed",
        created_at=datetime.utcnow(),
    )
    db.add(doc)
    await db.flush()

    # Document Chunks
    chunk1 = DocumentChunk(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        project_id=project.id,
        chunk_index=1,
        section_title="1.0 System Overview & Objectives",
        page_number=1,
        content="We need a platform where university students can find tutors, book sessions, pay online, and receive notifications. Tutors should manage their availability. Admin should monitor users and bookings. The platform should be secure and fast.",
        token_count=45,
    )
    chunk2 = DocumentChunk(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        project_id=project.id,
        chunk_index=2,
        section_title="2.0 Booking & Cancellation Policies",
        page_number=2,
        content="Students can cancel a booking at any time without restriction. All booking cancellations must be refunded immediately to student balance. Note: In section 4.2, bookings cannot be cancelled within 24 hours of session start.",
        token_count=42,
    )
    db.add_all([chunk1, chunk2])

    # 4. Requirements (FRs and NFRs grounded in source)
    reqs = [
        Requirement(
            id="FR-001",
            project_id=project.id,
            req_type="functional",
            summary="Student & Tutor Account Registration",
            description="Students and tutors shall register using valid university email credentials (.edu) with email verification.",
            actor="Student",
            action="register and authenticate",
            target_object="User Account",
            preconditions="User has valid university email",
            expected_outcome="Account created and verification token sent",
            acceptance_criteria=[
                "Given a user with .edu email, When submitted, Then verification link sent",
                "Given invalid email domain, When submitted, Then show error"
            ],
            priority="high",
            status="approved",
            quality_score=92.0,
            quality_breakdown={"completeness": 95, "clarity": 90, "atomicity": 95, "consistency": 90, "testability": 90, "feasibility": 95, "traceability": 100},
            confidence=0.96,
            is_ai_suggested=False,
            source_id="Tutor_Booking_Platform_RFP_Specification.pdf",
            source_page=1,
            source_excerpt="students can find tutors, book sessions, pay online... using valid university email",
        ),
        Requirement(
            id="FR-002",
            project_id=project.id,
            req_type="functional",
            summary="Tutor Search & Subject Filtering",
            description="Students shall search for tutors filtered by academic subject, hourly pricing, rating score, and calendar availability.",
            actor="Student",
            action="search and filter",
            target_object="Tutor Directory",
            preconditions="User is logged in",
            expected_outcome="Filtered list of eligible tutors returned in under 500ms",
            acceptance_criteria=[
                "Given search query for 'Calculus', When executed, Then return all calculus tutors",
                "Given filter by rating > 4.5, When applied, Then list updates immediately"
            ],
            priority="high",
            status="approved",
            quality_score=89.0,
            quality_breakdown={"completeness": 90, "clarity": 85, "atomicity": 90, "consistency": 90, "testability": 85, "feasibility": 90, "traceability": 100},
            confidence=0.94,
            is_ai_suggested=False,
            source_id="Tutor_Booking_Platform_RFP_Specification.pdf",
            source_page=1,
            source_excerpt="students can find tutors, book sessions",
        ),
        Requirement(
            id="FR-003",
            project_id=project.id,
            req_type="functional",
            summary="Session Slot Reservation & Double-Booking Guard",
            description="Students shall select open time slots and reserve a tutoring session; system must acquire a mutex lock to prevent concurrent double-booking.",
            actor="Student",
            action="reserve session",
            target_object="Tutoring Slot",
            preconditions="Tutor marked slot as available",
            expected_outcome="Session placed in pending payment state for 10 minutes",
            acceptance_criteria=[
                "Given two simultaneous booking attempts for same slot, When submitted, Then only first succeeds and second receives slot taken error"
            ],
            priority="critical",
            status="approved",
            quality_score=94.0,
            quality_breakdown={"completeness": 95, "clarity": 95, "atomicity": 90, "consistency": 95, "testability": 95, "feasibility": 90, "traceability": 100},
            confidence=0.98,
            is_ai_suggested=False,
            source_id="Tutor_Booking_Platform_RFP_Specification.pdf",
            source_page=1,
            source_excerpt="book sessions, pay online... Tutors should manage their availability",
        ),
        Requirement(
            id="FR-004",
            project_id=project.id,
            req_type="functional",
            summary="Online Escrow Payment & Payout",
            description="The platform shall process credit card payments via Stripe escrow; funds held until session completion confirmation.",
            actor="Student",
            action="pay for session",
            target_object="Payment Escrow",
            preconditions="Session slot reserved",
            expected_outcome="Payment authorized, receipt emailed, and payout queued for tutor",
            acceptance_criteria=[
                "Given valid card payment, When authorized, Then session state changes to 'Confirmed'",
                "Given payment failure, When declined, Then release reservation slot"
            ],
            priority="high",
            status="approved",
            quality_score=91.0,
            quality_breakdown={"completeness": 90, "clarity": 90, "atomicity": 90, "consistency": 90, "testability": 95, "feasibility": 90, "traceability": 100},
            confidence=0.95,
            is_ai_suggested=False,
            source_id="Tutor_Booking_Platform_RFP_Specification.pdf",
            source_page=1,
            source_excerpt="pay online, and receive notifications",
        ),
        Requirement(
            id="FR-005",
            project_id=project.id,
            req_type="functional",
            summary="Real-Time Booking Notifications",
            description="The system shall dispatch email and in-app push notifications to both tutor and student upon booking creation, rescheduling, or cancellation.",
            actor="System",
            action="dispatch alerts",
            target_object="Notification Center",
            preconditions="Booking state event triggered",
            expected_outcome="Alert dispatched within 5 seconds",
            acceptance_criteria=[
                "Given booking confirmed, When event fired, Then both parties receive push notification"
            ],
            priority="medium",
            status="approved",
            quality_score=88.0,
            quality_breakdown={"completeness": 85, "clarity": 90, "atomicity": 90, "consistency": 90, "testability": 85, "feasibility": 90, "traceability": 100},
            confidence=0.92,
            is_ai_suggested=False,
            source_id="Tutor_Booking_Platform_RFP_Specification.pdf",
            source_page=1,
            source_excerpt="receive notifications. Tutors should manage their availability",
        ),
        Requirement(
            id="FR-006",
            project_id=project.id,
            req_type="functional",
            summary="Unrestricted Session Cancellation Policy",
            description="Students can cancel a booking at any time without restriction and receive immediate full refund.",
            actor="Student",
            action="cancel booking",
            target_object="Booking Record",
            preconditions="Active booking exists",
            expected_outcome="Booking cancelled and full balance returned",
            acceptance_criteria=["Given an upcoming booking, When student clicks cancel, Then cancellation is confirmed instantly"],
            priority="high",
            status="needs_review",
            quality_score=76.0,
            quality_breakdown={"completeness": 80, "clarity": 80, "atomicity": 85, "consistency": 50, "testability": 85, "feasibility": 80, "traceability": 100},
            confidence=0.88,
            is_ai_suggested=False,
            source_id="Tutor_Booking_Platform_RFP_Specification.pdf",
            source_page=2,
            source_excerpt="Students can cancel a booking at any time without restriction.",
        ),
        Requirement(
            id="FR-007",
            project_id=project.id,
            req_type="functional",
            summary="24-Hour Cancellation Restriction Policy",
            description="Bookings cannot be cancelled within 24 hours of session start time to protect tutor scheduling commitments.",
            actor="Student",
            action="cancel booking",
            target_object="Booking Record",
            preconditions="Booking is within 24 hours of scheduled start",
            expected_outcome="Cancellation blocked with notification policy displayed",
            acceptance_criteria=["Given booking < 24h away, When cancellation requested, Then system displays non-cancellable policy error"],
            priority="high",
            status="needs_review",
            quality_score=78.0,
            quality_breakdown={"completeness": 85, "clarity": 85, "atomicity": 85, "consistency": 50, "testability": 90, "feasibility": 85, "traceability": 100},
            confidence=0.90,
            is_ai_suggested=False,
            source_id="Tutor_Booking_Platform_RFP_Specification.pdf",
            source_page=2,
            source_excerpt="In section 4.2, bookings cannot be cancelled within 24 hours of session start.",
        ),
        Requirement(
            id="NFR-001",
            project_id=project.id,
            req_type="non_functional",
            summary="Authentication Security & Role-Based Isolation",
            description="Authentication shall use JWT tokens signed with HS256/RS256, passwords hashed with bcrypt (cost factor >= 12), and role-based access control.",
            actor="System",
            action="enforce security",
            target_object="Auth Token",
            preconditions="All API requests",
            expected_outcome="Unauthorized requests rejected with HTTP 401/403",
            acceptance_criteria=["Given expired token, When API called, Then return 401 Unauthorized"],
            priority="critical",
            status="approved",
            quality_score=96.0,
            quality_breakdown={"completeness": 95, "clarity": 95, "atomicity": 95, "consistency": 95, "testability": 100, "feasibility": 95, "traceability": 100},
            confidence=0.97,
            is_ai_suggested=False,
            source_id="Tutor_Booking_Platform_RFP_Specification.pdf",
            source_page=1,
            source_excerpt="The platform should be secure and fast.",
        ),
        Requirement(
            id="NFR-002",
            project_id=project.id,
            req_type="non_functional",
            summary="High Performance Response Latency",
            description="The system API response time must be fast under 500 concurrent active users.",
            actor="System",
            action="respond quickly",
            target_object="API Responses",
            preconditions="Normal load",
            expected_outcome="System should be fast",
            acceptance_criteria=["Verify system is fast"],
            priority="medium",
            status="needs_review",
            quality_score=62.0,
            quality_breakdown={"completeness": 60, "clarity": 40, "atomicity": 80, "consistency": 90, "testability": 50, "feasibility": 80, "traceability": 100},
            confidence=0.82,
            is_ai_suggested=False,
            source_id="Tutor_Booking_Platform_RFP_Specification.pdf",
            source_page=1,
            source_excerpt="The platform should be secure and fast.",
        ),
    ]
    db.add_all(reqs)

    # 5. Issues (Ambiguity, Conflict, Duplicate)
    issues = [
        RequirementIssue(
            id=str(uuid.uuid4()),
            project_id=project.id,
            requirement_id="NFR-002",
            issue_type="ambiguity",
            title="Ambiguous performance specification: 'fast'",
            description="The requirement states the system should be 'fast' without specifying quantitative SLA thresholds (e.g. p95 < 200ms).",
            detected_phrase="fast",
            severity="medium",
            confidence=0.92,
            status="open",
        ),
        RequirementIssue(
            id=str(uuid.uuid4()),
            project_id=project.id,
            requirement_id="FR-006",
            conflict_with_id="FR-007",
            issue_type="conflict",
            title="Contradictory Cancellation Rules (FR-006 vs FR-007)",
            description="FR-006 explicitly permits cancellation 'at any time without restriction' whereas FR-007 states 'bookings cannot be cancelled within 24 hours of session start'.",
            detected_phrase="cancel at any time vs cannot cancel within 24h",
            severity="high",
            confidence=0.96,
            status="open",
        ),
        RequirementIssue(
            id=str(uuid.uuid4()),
            project_id=project.id,
            requirement_id="NFR-001",
            issue_type="ambiguity",
            title="Subjective requirement phrasing: 'secure'",
            description="The term 'secure' requires specific encryption cipher suites and compliance standards to be legally and technically testable.",
            detected_phrase="secure",
            severity="medium",
            confidence=0.88,
            status="open",
        )
    ]
    db.add_all(issues)

    # 6. Clarifications
    clarifs = [
        ClarificationQuestion(
            id=str(uuid.uuid4()),
            project_id=project.id,
            requirement_id="NFR-002",
            question="What maximum response time should be targeted for tutor search and booking operations under peak load?",
            rationale="Quantifying 'fast' ensures engineering performance targets can be benchmarked.",
            priority="high",
            suggested_options=["p95 < 250ms for search; p99 < 500ms for bookings", "< 1 second for all endpoints", "< 2 seconds under peak load"],
            status="pending",
        ),
        ClarificationQuestion(
            id=str(uuid.uuid4()),
            project_id=project.id,
            requirement_id="FR-006",
            question="How should the contradiction between unrestricted cancellation (FR-006) and the 24-hour cutoff (FR-007) be resolved?",
            rationale="Contradictory business rules block implementation of the booking cancellation API.",
            priority="high",
            suggested_options=[
                "Free cancellation up to 24 hours before session; 50% refund between 2-24 hours; no refund under 2 hours",
                "Allow cancellation anytime with full refund (student-friendly)",
                "Strict 24-hour non-refundable policy (tutor-friendly)"
            ],
            status="pending",
        )
    ]
    db.add_all(clarifs)

    # 7. Architecture Modules & Relations
    modules = [
        ArchitectureModule(
            id="MOD-GATEWAY", project_id=project.id, name="API Gateway & Rate Limiter",
            description="Edge reverse proxy, SSL termination, and request throttling.",
            module_type="gateway", tech_stack="Nginx / Traefik",
            responsibilities=["Route routing", "Rate limiting (100 req/min)", "SSL termination"],
            api_endpoints=["/api/v1/*"], pos_x=450.0, pos_y=60.0
        ),
        ArchitectureModule(
            id="MOD-AUTH", project_id=project.id, name="Auth & Identity Provider",
            description="User credentials, JWT issuance, password hashing, and session management.",
            module_type="service", tech_stack="FastAPI / PyJWT / bcrypt",
            responsibilities=["Registration", "Login", "Token Refresh", "Role Enforcement"],
            api_endpoints=["/api/auth/register", "/api/auth/login", "/api/auth/me"], pos_x=180.0, pos_y=200.0
        ),
        ArchitectureModule(
            id="MOD-USER", project_id=project.id, name="User & Tutor Profile Service",
            description="Tutor profiles, subject catalog, rating aggregation, and availability calendars.",
            module_type="service", tech_stack="FastAPI + PostgreSQL",
            responsibilities=["Profile management", "Tutor search & filters", "Availability slots"],
            api_endpoints=["/api/tutors/search", "/api/tutors/{id}/slots"], pos_x=450.0, pos_y=200.0
        ),
        ArchitectureModule(
            id="MOD-BOOKING", project_id=project.id, name="Session Booking Orchestrator",
            description="Slot reservation, concurrency locks, state transitions, and cancellation enforcement.",
            module_type="service", tech_stack="FastAPI + Redis Mutex",
            responsibilities=["Slot hold lock", "Reservation state machine", "Cancellation handler"],
            api_endpoints=["/api/bookings/reserve", "/api/bookings/{id}/cancel"], pos_x=720.0, pos_y=200.0
        ),
        ArchitectureModule(
            id="MOD-PAYMENT", project_id=project.id, name="Payment & Escrow Gateway",
            description="Credit card processing via Stripe, escrow holds, and automated tutor payouts.",
            module_type="service", tech_stack="Stripe API + Webhooks",
            responsibilities=["Card charge", "Escrow balance", "Refund dispatch", "Payout ledger"],
            api_endpoints=["/api/payments/intent", "/api/payments/webhook"], pos_x=720.0, pos_y=350.0
        ),
        ArchitectureModule(
            id="MOD-NOTIFY", project_id=project.id, name="Real-Time Notification Hub",
            description="Dispatches push notifications, email alerts, and WebSocket updates.",
            module_type="service", tech_stack="WebSocket / SendGrid / Redis PubSub",
            responsibilities=["Email alerts", "In-app notifications", "Session reminders"],
            api_endpoints=["/api/notifications/ws"], pos_x=450.0, pos_y=350.0
        ),
        ArchitectureModule(
            id="MOD-DB", project_id=project.id, name="Core Relational Database",
            description="ACID persistence with relational models and indexing.",
            module_type="database", tech_stack="PostgreSQL 16 + pgvector",
            responsibilities=["Transactional integrity", "Foreign keys", "Automated backups"],
            api_endpoints=["Internal port 5432"], pos_x=450.0, pos_y=490.0
        ),
    ]
    db.add_all(modules)

    relations = [
        ArchitectureRelation(id=str(uuid.uuid4()), project_id=project.id, source_module_id="MOD-GATEWAY", target_module_id="MOD-AUTH", relation_type="calls", description="Auth routing"),
        ArchitectureRelation(id=str(uuid.uuid4()), project_id=project.id, source_module_id="MOD-GATEWAY", target_module_id="MOD-USER", relation_type="calls", description="Profile routing"),
        ArchitectureRelation(id=str(uuid.uuid4()), project_id=project.id, source_module_id="MOD-GATEWAY", target_module_id="MOD-BOOKING", relation_type="calls", description="Booking routing"),
        ArchitectureRelation(id=str(uuid.uuid4()), project_id=project.id, source_module_id="MOD-BOOKING", target_module_id="MOD-PAYMENT", relation_type="calls", description="Escrow payment request"),
        ArchitectureRelation(id=str(uuid.uuid4()), project_id=project.id, source_module_id="MOD-BOOKING", target_module_id="MOD-NOTIFY", relation_type="publishes_to", description="Booking event alert"),
        ArchitectureRelation(id=str(uuid.uuid4()), project_id=project.id, source_module_id="MOD-PAYMENT", target_module_id="MOD-NOTIFY", relation_type="publishes_to", description="Payment receipt alert"),
        ArchitectureRelation(id=str(uuid.uuid4()), project_id=project.id, source_module_id="MOD-AUTH", target_module_id="MOD-DB", relation_type="reads_from", description="Credentials & accounts"),
        ArchitectureRelation(id=str(uuid.uuid4()), project_id=project.id, source_module_id="MOD-USER", target_module_id="MOD-DB", relation_type="reads_from", description="Tutor profiles"),
        ArchitectureRelation(id=str(uuid.uuid4()), project_id=project.id, source_module_id="MOD-BOOKING", target_module_id="MOD-DB", relation_type="reads_from", description="Session state & bookings"),
    ]
    db.add_all(relations)

    # 8. Team Members with Skills (Section 29)
    team = [
        TeamMember(
            id=str(uuid.uuid4()), project_id=project.id, name="Sarah Chen", email="sarah.chen@reqpilot.ai",
            role="Senior Backend Engineer", capacity_hours_per_week=40.0, current_load_pct=65.0,
            skills={"Python": 95, "FastAPI": 92, "PostgreSQL": 90, "Redis": 85, "Security": 88}
        ),
        TeamMember(
            id=str(uuid.uuid4()), project_id=project.id, name="Marcus Vance", email="marcus.v@reqpilot.ai",
            role="Frontend & UI Lead", capacity_hours_per_week=40.0, current_load_pct=50.0,
            skills={"React": 94, "TypeScript": 90, "Tailwind": 95, "WebSocket": 80, "HTML/CSS": 95}
        ),
        TeamMember(
            id=str(uuid.uuid4()), project_id=project.id, name="Priya Patel", email="priya.p@reqpilot.ai",
            role="Full Stack & Payments Specialist", capacity_hours_per_week=40.0, current_load_pct=70.0,
            skills={"Stripe": 95, "Python": 88, "FastAPI": 85, "React": 80, "Security": 85}
        ),
        TeamMember(
            id=str(uuid.uuid4()), project_id=project.id, name="Liam Gallagher", email="liam.g@reqpilot.ai",
            role="QA & Test Automation Lead", capacity_hours_per_week=40.0, current_load_pct=45.0,
            skills={"PyTest": 95, "Selenium": 90, "Security": 85, "Integration": 92, "Python": 85}
        ),
    ]
    db.add_all(team)

    # 9. Epics, Features, and Tasks (Section 13 & 28)
    epic1 = Epic(id="EPIC-01", project_id=project.id, title="User Authentication & Security", description="Registration, JWT auth, and RBAC", status="in_progress")
    epic2 = Epic(id="EPIC-02", project_id=project.id, title="Tutor Discovery & Profiles", description="Search, filtering, and tutor availability", status="in_progress")
    epic3 = Epic(id="EPIC-03", project_id=project.id, title="Session Reservation & Booking", description="Slot booking with concurrency locks", status="in_progress")
    epic4 = Epic(id="EPIC-04", project_id=project.id, title="Financial Payments & Escrow", description="Stripe checkout and escrow holding", status="in_progress")
    db.add_all([epic1, epic2, epic3, epic4])
    await db.flush()

    tasks = [
        Task(
            id="TASK-001", project_id=project.id, epic_id=epic1.id, requirement_id="FR-001", module_id="MOD-AUTH",
            title="Implement User Registration & JWT Auth API", description="Build signup, login, password hashing with bcrypt, and JWT token issue.",
            complexity="medium", estimated_hours=12.0, story_points=3, priority="high", status="done",
            assignee_name="Sarah Chen", sprint_name="Sprint 1",
            subtasks=["Create user model & schema", "Implement bcrypt password hashing", "Create JWT token generation endpoint"],
            acceptance_criteria=["Valid credentials return 200 with JWT access token", "Passwords salted and hashed securely"]
        ),
        Task(
            id="TASK-002", project_id=project.id, epic_id=epic2.id, requirement_id="FR-002", module_id="MOD-USER",
            title="Build Tutor Search & Multi-Filter Endpoints", description="Implement search query filters by subject, rating, price, and date range.",
            complexity="medium", estimated_hours=10.0, story_points=3, priority="high", status="in_progress",
            assignee_name="Marcus Vance", sprint_name="Sprint 1",
            subtasks=["Design search indexing query", "Build query parameter filter handlers", "Integrate frontend tutor card list"],
            acceptance_criteria=["Search filters return matched tutor profiles within 300ms"]
        ),
        Task(
            id="TASK-003", project_id=project.id, epic_id=epic3.id, requirement_id="FR-003", module_id="MOD-BOOKING",
            title="Implement Session Reservation with Redis Mutex Lock", description="Prevent concurrent double-booking by acquiring distributed lock during slot reservation.",
            complexity="high", estimated_hours=16.0, story_points=5, priority="critical", status="todo",
            assignee_name="Sarah Chen", sprint_name="Sprint 1",
            subtasks=["Implement Redis distributed lock helper", "Build slot reservation endpoint with 10-minute TTL", "Handle race condition tests"],
            acceptance_criteria=["Simultaneous reservation attempts cannot reserve identical slot"]
        ),
        Task(
            id="TASK-004", project_id=project.id, epic_id=epic4.id, requirement_id="FR-004", module_id="MOD-PAYMENT",
            title="Integrate Stripe Escrow & Webhook Receiver", description="Create Stripe checkout sessions, hold payment in escrow, and handle webhook events.",
            complexity="high", estimated_hours=18.0, story_points=5, priority="high", status="todo",
            assignee_name="Priya Patel", sprint_name="Sprint 2",
            subtasks=["Setup Stripe SDK credentials", "Create payment intent endpoint", "Build webhook handler for payment_intent.succeeded"],
            acceptance_criteria=["Successful payment updates booking state to 'Confirmed'"]
        ),
        Task(
            id="TASK-005", project_id=project.id, epic_id=epic3.id, requirement_id="FR-005", module_id="MOD-NOTIFY",
            title="Build Real-Time Push & Email Dispatcher", description="Emit real-time WebSocket messages and transactional emails for session events.",
            complexity="low", estimated_hours=8.0, story_points=2, priority="medium", status="todo",
            assignee_name="Marcus Vance", sprint_name="Sprint 2",
            subtasks=["Create notification WebSocket manager", "Build email dispatch worker with template"],
            acceptance_criteria=["Both student and tutor receive email upon confirmation"]
        ),
    ]
    db.add_all(tasks)

    # 10. Test Cases (Section 14)
    tests = [
        TestCase(
            id="TEST-001", project_id=project.id, requirement_id="FR-001", task_id="TASK-001",
            title="Registration & Token Verification Test", test_type="integration",
            preconditions="Database online", steps=["POST /api/auth/register", "POST /api/auth/login", "Verify JWT payload"],
            expected_result="User registered and token verified", status="not_run"
        ),
        TestCase(
            id="TEST-002", project_id=project.id, requirement_id="FR-002", task_id="TASK-002",
            title="Tutor Search & Filtering Response Time Test", test_type="performance",
            preconditions="100 tutors seeded", steps=["GET /api/tutors/search?subject=Math&rating=4"],
            expected_result="Response time < 300ms with filtered results", status="not_run"
        ),
        TestCase(
            id="TEST-003", project_id=project.id, requirement_id="FR-003", task_id="TASK-003",
            title="Concurrent Double-Booking Mutex Test", test_type="integration",
            preconditions="1 open slot", steps=["Execute 2 simultaneous POST /api/bookings/reserve for same slot"],
            expected_result="1 succeeded with 200, 1 rejected with 409 Conflict", status="not_run"
        ),
    ]
    db.add_all(tests)

    # 11. Sprints
    sprints = [
        Sprint(id=str(uuid.uuid4()), project_id=project.id, name="Sprint 1", goal="Core Auth, Tutor Discovery & Booking Lock", start_date="2026-09-01", end_date="2026-09-14", capacity_points=25, status="active"),
        Sprint(id=str(uuid.uuid4()), project_id=project.id, name="Sprint 2", goal="Payment Escrow & Notifications Hub", start_date="2026-09-15", end_date="2026-09-28", capacity_points=25, status="planning"),
        Sprint(id=str(uuid.uuid4()), project_id=project.id, name="Sprint 3", goal="Cancellation Policy & Telemetry Dashboard", start_date="2026-09-29", end_date="2026-10-12", capacity_points=25, status="planning"),
    ]
    db.add_all(sprints)

    # 12. Change Request Sample (Section 15 & 30 Killer Feature Demonstration)
    cr = ChangeRequest(
        id="CR-001",
        project_id=project.id,
        requirement_id="FR-006",
        title="Harmonize Cancellation Policy to 2-Hour Tiered Cutoff",
        description="Replace conflicting unrestricted cancellation with a 2-hour tiered cutoff: 100% refund > 24h, 50% refund between 2-24h, 0% refund < 2h.",
        proposed_summary="Tiered Session Cancellation Policy with 2-Hour Minimum Cutoff",
        proposed_description="Students may cancel bookings with full refund up to 24 hours before the session. Cancellations between 2 and 24 hours incur a 50% late cancellation fee. No cancellations permitted within 2 hours of session start.",
        risk_level="medium",
        schedule_impact="Medium (+3 to 5 Days)",
        status="pending",
    )
    db.add(cr)
    await db.flush()

    impacts = [
        ImpactItem(id=str(uuid.uuid4()), change_request_id=cr.id, artifact_type="requirement", artifact_id="FR-007", artifact_name="24-Hour Cancellation Restriction Policy", impact_description="Replaced by unified tiered rule.", severity="medium"),
        ImpactItem(id=str(uuid.uuid4()), change_request_id=cr.id, artifact_type="module", artifact_id="MOD-BOOKING", artifact_name="Session Booking Orchestrator", impact_description="Cancellation state machine must check 2h and 24h thresholds.", severity="high"),
        ImpactItem(id=str(uuid.uuid4()), change_request_id=cr.id, artifact_type="module", artifact_id="MOD-PAYMENT", artifact_name="Payment & Escrow Gateway", impact_description="Escrow refund calculation must support partial 50% penalty refund.", severity="high"),
        ImpactItem(id=str(uuid.uuid4()), change_request_id=cr.id, artifact_type="task", artifact_id="TASK-003", artifact_name="Implement Session Reservation with Redis Mutex Lock", impact_description="Update booking status logic.", severity="medium"),
        ImpactItem(id=str(uuid.uuid4()), change_request_id=cr.id, artifact_type="task", artifact_id="TASK-004", artifact_name="Integrate Stripe Escrow & Webhook Receiver", impact_description="Add partial refund execution call in Stripe handler.", severity="high"),
        ImpactItem(id=str(uuid.uuid4()), change_request_id=cr.id, artifact_type="test", artifact_id="TEST-003", artifact_name="Concurrent Double-Booking Mutex Test", impact_description="Add 3 new test cases for tiered cancellation scenarios.", severity="medium"),
    ]
    db.add_all(impacts)

    await db.commit()
