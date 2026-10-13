import os
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

print("Starting surgical correction sprint on ReqPilot_AI_Project_Report.docx...")

src_docx = r"c:\Users\ch.nayanesh reddy\Downloads\ReqPilot_AI_recovered_audited\fsd_pro\report_output\ReqPilot_AI_Project_Report.docx"
out_docx = r"c:\Users\ch.nayanesh reddy\Downloads\ReqPilot_AI_recovered_audited\fsd_pro\report_output\ReqPilot_AI_Project_Report_Corrected.docx"

doc = docx.Document(src_docx)
print(f"Loaded document: {len(doc.paragraphs)} paragraphs, {len(doc.tables)} tables.")

ns = nsdecls("w")

# =========================================================================
# 1. TABLE 3.1: Table Formatting (cantSplit & tblHeader)
# =========================================================================
t31 = doc.tables[1]
t31.rows[0]._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {ns}/>'))
for r in t31.rows:
    r._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {ns}/>'))
print("Table 3.1 repetition and cantSplit applied.")

# =========================================================================
# 2. TABLE 4.1: Line-wrapping & cantSplit
# =========================================================================
t41 = doc.tables[3]
t41.rows[0]._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {ns}/>'))
for r in t41.rows:
    r._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {ns}/>'))
# Check row 10 endpoint text: wrap cleanly
c_ep = t41.rows[10].cells[1]
if "/api/projects/{id}/change-impact/simulate" in c_ep.text:
    c_ep.text = "/api/projects/{id}/\nchange-impact/simulate"
    c_ep.paragraphs[0].runs[0].font.name = "Times New Roman"
    c_ep.paragraphs[0].runs[0].font.size = Pt(9.5)
print("Table 4.1 line-wrapping and cantSplit applied.")

# =========================================================================
# 3. TABLE 4.2: Caption, cantSplit, and Scope Clarification
# =========================================================================
t42 = doc.tables[4]
t42.rows[0]._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {ns}/>'))
for r in t42.rows:
    r._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {ns}/>'))

# Find Table 4.2 caption paragraph and preceding prose
for p in doc.paragraphs:
    if "Table 4.2 documents the primary fields" in p.text:
        p.text = (
            "Table 4.2 documents the primary fields, data types, and foreign key relationships of selected core database entities. "
            "The active persistence layer implements a comprehensive relational schema comprising twenty-three tables managed via "
            "SQLAlchemy 2.0 Async ORM with SQLite (aiosqlite) and PostgreSQL compatibility: users, projects, documents, document_chunks, "
            "requirements, requirement_versions, requirement_issues, clarification_questions, architecture_modules, architecture_relations, "
            "epics, features, tasks, task_dependencies, sprints, team_members, impact_items, change_requests, test_cases, traceability_links, "
            "reports, audit_logs, and ai_workflows."
        )
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
    elif "Table 4.2 – Core database entity specifications" in p.text:
        p.text = "Table 4.2 – Selected core database entity specifications and relational constraints"
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            r.font.italic = True
print("Table 4.2 scope and caption updated.")

# =========================================================================
# 4. TABLES 6.1 and 6.2: Formatting & Headers
# =========================================================================
t61 = doc.tables[9]
t61.rows[0]._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {ns}/>'))
for r in t61.rows:
    r._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {ns}/>'))

t62 = doc.tables[10]
t62.rows[0]._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {ns}/>'))
for r in t62.rows:
    r._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {ns}/>'))
print("Tables 6.1 and 6.2 headers and cantSplit applied.")

# =========================================================================
# 5. TEXT CORRECTIONS: Chapters 1, 2, 3, 4, 5, 6, 7
# =========================================================================

for p in doc.paragraphs:
    # Page 2-3 / Chapter 1: Grammatical error & claims
    if "an production-grade modular workspace" in p.text:
        p.text = p.text.replace("an production-grade modular workspace", "a production-grade modular workspace")
        for r in p.runs:
            r.font.name = "Times New Roman"
    
    if "This multi-tier architecture ensures that every analytical insight is explainable" in p.text:
        p.text = p.text.replace(
            "This multi-tier architecture ensures that every analytical insight is explainable, mathematically auditable, and grounded in verifiable source document excerpts.",
            "This multi-tier architecture ensures that analytical insights are traceable, structurally auditable, and grounded in verifiable source document excerpts where direct textual evidence exists."
        )
        for r in p.runs:
            r.font.name = "Times New Roman"

    # Standish Group citation verification
    if "The Standish Group Chaos Report has persistently revealed" in p.text:
        p.text = (
            "Empirical software engineering literature has consistently documented that a substantial fraction of software development projects "
            "experience budget overruns, timeline delays, or outright cancellation, with flawed, ambiguous, and shifting requirements identified "
            "as primary contributing factors [1], [7], [9]. While modern developer tooling has heavily automated continuous integration, "
            "containerized deployment, and code generation, the upstream requirements engineering phase remains manual and frequently fragmented "
            "across generic word processors and disconnected spreadsheet trackers."
        )
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)

    # Chapter 2: Absolute claims
    if "Standard word processors provide basic grammatical spell-checking but possess zero semantic awareness" in p.text:
        p.text = (
            "2. Inability to Detect Latent Ambiguities: Standard word processors provide grammatical and orthographic checks but lack "
            "specialized requirements-engineering semantic validation. Subjective adjectives like 'the system must scale smoothly' pass through "
            "manual walkthroughs unnoticed, resulting in costly re-engineering during performance testing [13]."
        )
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)

    if "ReqPilot AI introduces a fundamentally superior architectural approach" in p.text:
        p.text = (
            "ReqPilot AI introduces a cohesive architectural approach by establishing an integrated Multi-Agent Cooperative Engineering Fabric. "
            "Rather than relying solely on brittle rule-based parsers or unconstrained stochastic LLM generators, ReqPilot AI couples structured "
            "natural language reasoning with deterministic validation rules within a schema-validated execution pipeline [17]."
        )
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)

    if "traverse the relational graph to identify affected artifacts with zero human guesswork" in p.text:
        p.text = p.text.replace(
            "traverse the relational graph to identify affected artifacts with zero human guesswork",
            "traverse relational linkages to identify candidate affected artifacts for human engineering review"
        )
        for r in p.runs:
            r.font.name = "Times New Roman"

    # Chapter 3: Major features vs workspaces vs agents
    if "The ReqPilot AI platform comprises nine core functional modules" in p.text:
        p.text = (
            "The platform architecture organizes system functionality into a clear hierarchy: nine core functional capability domains, "
            "ten interactive frontend workspace tabs (Overview, Sources, Requirements, Issues, Clarifications, Architecture, Planning, "
            "Traceability, Change Impact, and Reports), and fifteen specialized cooperative backend agents coordinated across an "
            "eight-step execution pipeline:"
        )
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)

    # Chapter 3: Performance & Security targets
    if "1. Performance (NFR-01): The frontend dashboard shall render" in p.text:
        p.text = (
            "1. Performance Target (NFR-01): Specified operational performance targets mandate that the frontend dashboard renders "
            "analytical tabs within 300 ms, backend API endpoints respond within a targeted 250 ms p95 latency under standard local workloads, "
            "and document chunking with heuristic extraction for a 15-requirement document targets completion within 2.5 seconds. "
            "Measured end-to-end multi-agent pipeline durations range between 33 and 46 seconds on full multi-page benchmark specifications "
            "when external cloud LLM reasoning and rate-limited slot cooldowns are active."
        )
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in r.runs if hasattr(r, 'runs') else p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)

    if "Input sanitization shall neutralize prompt injection tokens." in p.text:
        p.text = p.text.replace(
            "Input sanitization shall neutralize prompt injection tokens.",
            "Input sanitization regex-filters known prompt injection phrases (e.g., 'ignore previous instructions') from untrusted document text prior to LLM submission, mitigating direct prompt override attempts."
        )
        for r in p.runs:
            r.font.name = "Times New Roman"

    # Chapter 3: Smart Campus illustrative test fixture
    if "1. User uploads 'SMART CAMPUS MANAGEMENT SYSTEM.docx'." in p.text:
        p.text = (
            "1. User uploads 'SMART CAMPUS MANAGEMENT SYSTEM.docx' (an illustrative multi-stakeholder specification test fixture)."
        )
        for r in p.runs:
            r.font.name = "Times New Roman"

    # Chapter 4: Figure 4.1 & 4.3 labels
    if "Figure 4.1 – Overall system architecture of the ReqPilot AI full-stack platform" in p.text:
        p.text = "Figure 4.1 – High-level multi-tier system architecture of the ReqPilot AI platform"
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            r.font.italic = True

    if "Figure 4.3 – Entity-Relationship (ER) diagram of the ReqPilot AI database" in p.text:
        p.text = "Figure 4.3 – Conceptual Entity-Relationship (ER) diagram of core ReqPilot AI database entities"
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            r.font.italic = True

    # Chapter 5: Repeated modern
    if "utilizes modern, robust, modern open-source technologies" in p.text:
        p.text = p.text.replace("utilizes modern, robust, modern open-source technologies", "utilizes robust open-source technologies")
        for r in p.runs:
            r.font.name = "Times New Roman"

    # Chapter 5: Listing 5.2 & 5.3 descriptions
    if "Listing 5.2 – NetworkX Directed Acyclic Graph" in p.text:
        p.text = "Listing 5.2 – NetworkX DAG Task Scheduling with Fallback Handling (scheduling_agent.py excerpt)"
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            r.font.bold = True

    if "Listing 5.3 – Change Impact Blast-Radius" in p.text:
        p.text = "Listing 5.3 – Change Impact Blast-Radius and Heuristic Risk Assessment (change_impact_agent.py excerpt)"
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            r.font.bold = True

    # Chapter 6: Macro-F1 clarification & test details
    if "Automated unit, integration, and regression test suites were executed" in p.text:
        p.text = (
            "Automated unit, integration, and regression test suites were executed across the platform using pytest 8.3 and httpx. "
            "The test harness spans 46 comprehensive test cases covering multi-agent cognitive services (QualityAgent, AmbiguityAgent, "
            "ConflictAgent, DuplicateAgent, SchedulingAgent, ChangeImpactAgent), FastAPI REST endpoints, and dynamic module preservation "
            "(test_agents.py, test_workflow.py, test_classification_remediation.py, and test_dynamic_modules.py). "
            "All 46 unit and regression tests executed with zero failures (46 passed, 16 deprecation warnings in 10.09s on 2026-10-14). "
            "Table 6.1 details the functional test execution matrix across core platform components."
        )
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)

    if "Table 6.2 presents the official quantitative benchmark results" in p.text:
        p.text = (
            "Table 6.2 presents the official quantitative benchmark results across all four retained domains from the verified evaluation snapshot, "
            "detailing run identifiers, gold requirement sample counts, matched denominators, classification accuracy, penalized end-to-end accuracy, "
            "and macro-F1. Aggregate macro-F1 is calculated as the unweighted arithmetic mean of individual domain macro-F1 scores (0.8710 across the four domains), "
            "treating each domain equally regardless of requirement count."
        )
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)

    # Chapter 7: Conclusion alignment
    if "4. Empirical demonstration of 94.41% aggregate classification accuracy" in p.text:
        p.text = (
            "4. Empirical demonstration of 94.41% aggregate matched classification accuracy (135/143 requirements correct) and 0.8710 average macro-F1 "
            "across four active industrial benchmark domains (EV Charging, E-Commerce Platform, Library Management, and Banking Management), "
            "supported by 46/46 passing automated unit and regression tests."
        )
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r in p.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)

    # Standish Group Reference entry
    if "[9] The Standish Group, \"The Chaos Report: Decision latency and project success,\"" in p.text:
        p.text = (
            "[9] The Standish Group, \"CHAOS Report 2015: Decision Latency and Project Success,\" Standish Group International, Boston, MA, Research Rep., 2015."
        )
        for r in p.runs:
            r.font.name = "Times New Roman"

print("All paragraph text corrections and semantic alignments applied.")

# =========================================================================
# 6. UPDATE TABLE 6.2 CONTENT (add Penalized column if appropriate)
# =========================================================================
# Table 6.2 currently has 7 columns: Project Domain, Run Identifier, Gold Reqs, Matched Denom, Correct Class, Accuracy (%), Macro-F1
# Let's verify and refine rows
t62_rows_data = [
    ("EV Charging", "9d9a6a23 (remediation)", "58", "58", "56", "96.55%", "0.9741"),
    ("E-Commerce Platform", "a0a716cb (remediation)", "36", "36", "35", "97.22%", "0.9677"),
    ("Library Management", "221074ed (remediation)", "24", "24", "23", "95.83%", "0.9604"),
    ("Banking Management", "1616700d (remediation)", "25", "25", "21", "84.00%", "0.5818"),
    ("Aggregate (4 Domains)", "Verified Official Suite", "143", "143", "135", "94.41%", "0.8710"),
]
for i, row in enumerate(t62_rows_data):
    for j, val in enumerate(row):
        c = t62.rows[i+1].cells[j]
        c.text = val
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT if j in [0, 1] else WD_ALIGN_PARAGRAPH.CENTER
        c.paragraphs[0].runs[0].font.name = "Times New Roman"
        c.paragraphs[0].runs[0].font.size = Pt(9.5)
        if i == len(t62_rows_data) - 1:
            c.paragraphs[0].runs[0].font.bold = True
            if j == 5:
                c.paragraphs[0].runs[0].font.color.rgb = RGBColor(30, 58, 138)

# =========================================================================
# 7. UPDATE CODE LISTINGS 5.2 and 5.3 TO ACCURATELY REFLECT REPOSITORY CODE
# =========================================================================
# Listing 5.2: SchedulingAgent excerpt with failure/cycle explanation
t_l52 = doc.tables[7]
t_l52.rows[0].cells[0].text = (
    "class SchedulingAgent:\n"
    "    \"\"\"Models task dependencies as a DAG and computes topological execution order (excerpt).\"\"\"\n"
    "    def schedule_tasks(self, tasks: List[Dict[str, Any]], dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:\n"
    "        G = nx.DiGraph()\n"
    "        for t in tasks:\n"
    "            G.add_node(t[\"id\"], title=t.get(\"title\", \"\"), points=t.get(\"story_points\", 3))\n"
    "        for d in dependencies:\n"
    "            G.add_edge(d[\"depends_on_task_id\"], d[\"task_id\"])\n"
    "\n"
    "        is_dag = nx.is_directed_acyclic_graph(G)\n"
    "        if is_dag:\n"
    "            # Valid acyclic dependency graph: compute optimal topological sprint execution order\n"
    "            order = list(nx.topological_sort(G))\n"
    "        else:\n"
    "            # Dependency cycle detected: returns original task sequence as a graceful fallback,\n"
    "            # flagged with is_valid_dag = False to alert engineering authorities of dependency deadlocks.\n"
    "            order = [t[\"id\"] for t in tasks]\n"
    "        return {\"is_valid_dag\": is_dag, \"execution_order\": order}"
)
p = t_l52.rows[0].cells[0].paragraphs[0]
p.runs[0].font.name = "Consolas"
p.runs[0].font.size = Pt(8.5)

# Listing 5.3: ChangeImpactAgent excerpt matching actual implementation
t_l53 = doc.tables[8]
t_l53.rows[0].cells[0].text = (
    "class ChangeImpactAgent:\n"
    "    \"\"\"Evidence-based change impact analysis traversing tasks, modules, and tests (excerpt).\"\"\"\n"
    "    def analyze_change(self, target_req_id: str, new_summary: str, new_description: str,\n"
    "                       all_requirements: List[Dict], all_modules: List[Dict],\n"
    "                       all_tasks: List[Dict], all_tests: List[Dict]) -> Dict[str, Any]:\n"
    "        # 1. Directly affected tasks linked via foreign key requirement_id\n"
    "        affected_tasks = [t for t in all_tasks if t.get(\"requirement_id\") == target_req_id]\n"
    "        # 2. Directly affected tests linked via requirement_id\n"
    "        affected_tests = [t for t in all_tests if t.get(\"requirement_id\") == target_req_id]\n"
    "        # 3. Architecture modules mapped through affected tasks\n"
    "        module_ids = {t.get(\"module_id\") for t in affected_tasks if t.get(\"module_id\")}\n"
    "        # 4. Related requirements identified via token similarity overlap (threshold >= 0.30)\n"
    "        related_reqs = self._find_related_requirements(target_req_id, new_summary, new_description, all_requirements)\n"
    "        # 5. Illustrative risk assessment heuristic based on artifact count and task complexity\n"
    "        total_affected = len(affected_tasks) + len(affected_tests) + len(module_ids) + len(related_reqs)\n"
    "        high_complexity = sum(1 for t in affected_tasks if str(t.get(\"complexity\") or \"\").lower() == \"high\")\n"
    "        risk = \"critical\" if (high_complexity >= 2 or total_affected >= 10) else (\"high\" if total_affected >= 5 else \"medium\")\n"
    "        schedule = \"High\" if risk == \"critical\" else (\"Medium\" if risk == \"high\" else \"Low\")\n"
    "        return {\"target_requirement_id\": target_req_id, \"risk_level\": risk, \"schedule_impact\": schedule,\n"
    "                \"summary_stats\": {\"affected_modules\": len(module_ids), \"affected_tasks\": len(affected_tasks),\n"
    "                                  \"affected_tests\": len(affected_tests), \"total_artifacts\": total_affected}}"
)
p = t_l53.rows[0].cells[0].paragraphs[0]
p.runs[0].font.name = "Consolas"
p.runs[0].font.size = Pt(8.5)

print("Listings 5.2 and 5.3 updated with exact repository logic.")

# Save corrected document
doc.save(out_docx)
print(f"Corrected document saved to: {out_docx}")
print(f"Size: {os.path.getsize(out_docx)} bytes")
