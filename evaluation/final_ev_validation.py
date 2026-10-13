import sqlite3
from collections import Counter
from pathlib import Path

from validate_ev_independent import (
    PROJECT_ID,
    EXPECTED_MODULE,
    CANONICAL_TO_DISPLAY,
    canonicalize_module_name,
    get_module_name,
    short_requirement_id,
)


DB = r".\backend\reqpilot.db"

RESULTS_DIR = Path(r".\evaluation\results")
REPORT_FILE = RESULTS_DIR / "EV_validation_report.txt"


def section(title):
    return "\n" + "=" * 110 + f"\n{title}\n" + "=" * 110


def main():

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    lines = []

    def log(message=""):
        print(message)
        lines.append(str(message))

    db = sqlite3.connect(DB)

    # ============================================================
    # 1. REQUIREMENT / TASK VALIDATION
    # ============================================================

    requirements = db.execute(
        """
        SELECT
            id,
            req_type,
            summary,
            description,
            source_excerpt,
            source_page
        FROM requirements
        WHERE project_id=?
        ORDER BY id
        """,
        (PROJECT_ID,),
    ).fetchall()

    tasks = db.execute(
        """
        SELECT
            id,
            requirement_id,
            module_id,
            epic_id,
            feature_id
        FROM tasks
        WHERE project_id=?
        ORDER BY id
        """,
        (PROJECT_ID,),
    ).fetchall()

    modules = db.execute(
        """
        SELECT
            id,
            name
        FROM architecture_modules
        WHERE project_id=?
        ORDER BY id
        """,
        (PROJECT_ID,),
    ).fetchall()

    # ============================================================
    # 2. BASIC PROJECT COUNTS
    # ============================================================

    log(
        section(
            "REQPILOT EV FINAL REPRODUCIBILITY VALIDATION"
        )
    )

    log(f"Project ID : {PROJECT_ID}")
    log(f"Database   : {DB}")

    log(section("PROJECT COUNTS"))

    project_counts = {}

    count_queries = {
        "Requirements":
            """
            SELECT COUNT(*)
            FROM requirements
            WHERE project_id=?
            """,

        "Architecture Modules":
            """
            SELECT COUNT(*)
            FROM architecture_modules
            WHERE project_id=?
            """,

        "Architecture Relations":
            """
            SELECT COUNT(*)
            FROM architecture_relations
            WHERE project_id=?
            """,

        "Epics":
            """
            SELECT COUNT(*)
            FROM epics
            WHERE project_id=?
            """,

        "Features":
            """
            SELECT COUNT(*)
            FROM features
            WHERE project_id=?
            """,

        "Tasks":
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE project_id=?
            """,

        "Task Dependencies":
            """
            SELECT COUNT(*)
            FROM task_dependencies
            WHERE task_id IN (
                SELECT id
                FROM tasks
                WHERE project_id=?
            )
            """,

        "Sprints":
            """
            SELECT COUNT(*)
            FROM sprints
            WHERE project_id=?
            """,

        "Test Cases":
            """
            SELECT COUNT(*)
            FROM test_cases
            WHERE project_id=?
            """,

        "Traceability Links":
            """
            SELECT COUNT(*)
            FROM traceability_links
            WHERE project_id=?
            """,

        "Reports":
            """
            SELECT COUNT(*)
            FROM reports
            WHERE project_id=?
            """,
    }

    for name, query in count_queries.items():

        value = db.execute(
            query,
            (PROJECT_ID,),
        ).fetchone()[0]

        project_counts[name] = value

        log(
            f"{name:25}: {value}"
        )

    # ============================================================
    # 3. INDEPENDENT SPECIFICATION-DERIVED ORACLE
    # ============================================================

    log(
        section(
            "INDEPENDENT SPECIFICATION-DERIVED ORACLE"
        )
    )

    oracle_missing = []
    source_missing = []
    predictions_missing = []
    matches = []

    prediction_rows = []

    for (
        rid,
        req_type,
        summary,
        description,
        source_excerpt,
        source_page,
    ) in requirements:

        short_id = short_requirement_id(rid)

        expected = EXPECTED_MODULE.get(short_id)

        if expected is None:
            oracle_missing.append(short_id)

        if not source_excerpt:
            source_missing.append(short_id)

        task_rows = [
            task
            for task in tasks
            if task[1] == rid
        ]

        if len(task_rows) == 0:

            predictions_missing.append(
                short_id
            )

            predicted = None
            predicted_name = None

        elif len(task_rows) > 1:

            predictions_missing.append(
                f"{short_id} "
                f"(multiple tasks: {len(task_rows)})"
            )

            predicted = None
            predicted_name = None

        else:

            predicted_module_id = task_rows[0][2]

            predicted_name = get_module_name(
                db,
                predicted_module_id,
            )

            predicted = canonicalize_module_name(
                predicted_name
            )

        match = (
            expected is not None
            and predicted is not None
            and expected == predicted
        )

        matches.append(match)

        prediction_rows.append(
            {
                "id": short_id,
                "expected": expected,
                "predicted": predicted,
                "predicted_name": predicted_name,
                "match": match,
            }
        )

    total = len(requirements)

    correct = sum(matches)

    accuracy = (
        correct / total * 100
        if total
        else 0.0
    )

    log(
        f"Requirements evaluated : {total}"
    )

    log(
        f"Oracle labels defined  : "
        f"{sum(1 for r in prediction_rows if r['expected'])}"
    )

    log(
        f"Correct classifications: {correct}"
    )

    log(
        f"Accuracy               : "
        f"{accuracy:.2f}%"
    )

    log(
        f"Missing oracle labels  : "
        f"{oracle_missing or 'NONE'}"
    )

    log(
        f"Missing source evidence: "
        f"{source_missing or 'NONE'}"
    )

    log(
        f"Missing/duplicate tasks: "
        f"{predictions_missing or 'NONE'}"
    )

    # ============================================================
    # 4. REQUIREMENT-LEVEL VALIDATION
    # ============================================================

    failures = [
        r
        for r in prediction_rows
        if not r["match"]
    ]

    log(
        section(
            "REQUIREMENT-LEVEL VALIDATION"
        )
    )

    if not failures:

        log(
            "ALL 58 REQUIREMENTS: PASS"
        )

    else:

        for row in failures:

            log(
                f"FAIL {row['id']}: "
                f"expected={row['expected']}, "
                f"predicted={row['predicted']}, "
                f"name={row['predicted_name']}"
            )

    # ============================================================
    # 5. PER-MODULE PRECISION / RECALL / F1
    # ============================================================

    labels = sorted(
        set(
            r["expected"]
            for r in prediction_rows
            if r["expected"]
        )
        |
        set(
            r["predicted"]
            for r in prediction_rows
            if r["predicted"]
        )
    )

    log(
        section(
            "PER-MODULE PRECISION / RECALL / F1"
        )
    )

    log(
        f"{'MODULE':30}"
        f"{'TP':>6}"
        f"{'FP':>6}"
        f"{'FN':>6}"
        f"{'PRECISION':>12}"
        f"{'RECALL':>10}"
        f"{'F1':>10}"
    )

    macro_precision = []
    macro_recall = []
    macro_f1 = []

    for label in labels:

        tp = sum(
            1
            for r in prediction_rows
            if r["expected"] == label
            and r["predicted"] == label
        )

        fp = sum(
            1
            for r in prediction_rows
            if r["expected"] != label
            and r["predicted"] == label
        )

        fn = sum(
            1
            for r in prediction_rows
            if r["expected"] == label
            and r["predicted"] != label
        )

        precision = (
            tp / (tp + fp)
            if (tp + fp)
            else 0.0
        )

        recall = (
            tp / (tp + fn)
            if (tp + fn)
            else 0.0
        )

        f1 = (
            2 * precision * recall
            / (precision + recall)
            if (precision + recall)
            else 0.0
        )

        macro_precision.append(
            precision
        )

        macro_recall.append(
            recall
        )

        macro_f1.append(
            f1
        )

        log(
            f"{CANONICAL_TO_DISPLAY.get(label, label):30}"
            f"{tp:6}"
            f"{fp:6}"
            f"{fn:6}"
            f"{precision:12.3f}"
            f"{recall:10.3f}"
            f"{f1:10.3f}"
        )

    macro_p = (
        sum(macro_precision)
        / len(macro_precision)
        if macro_precision
        else 0.0
    )

    macro_r = (
        sum(macro_recall)
        / len(macro_recall)
        if macro_recall
        else 0.0
    )

    macro_f = (
        sum(macro_f1)
        / len(macro_f1)
        if macro_f1
        else 0.0
    )

    log()

    log(
        f"Macro Precision : {macro_p:.3f}"
    )

    log(
        f"Macro Recall    : {macro_r:.3f}"
    )

    log(
        f"Macro F1        : {macro_f:.3f}"
    )

    # ============================================================
    # 6. CONFUSION MATRIX
    # ============================================================

    log(
        section(
            "CONFUSION MATRIX"
        )
    )

    matrix = Counter(
        (
            r["expected"],
            r["predicted"],
        )
        for r in prediction_rows
        if r["expected"]
        and r["predicted"]
    )

    off_diagonal = []

    for (
        expected,
        predicted,
    ), count in sorted(matrix.items()):

        if expected != predicted:

            off_diagonal.append(
                (
                    expected,
                    predicted,
                    count,
                )
            )

            log(
                f"{CANONICAL_TO_DISPLAY.get(expected, expected)}"
                f" -> "
                f"{CANONICAL_TO_DISPLAY.get(predicted, predicted)}"
                f" : {count}"
            )

    if not off_diagonal:

        log(
            "No off-diagonal classification errors."
        )

    # ============================================================
    # 7. TASK INTEGRITY
    # ============================================================

    log(
        section(
            "TASK INTEGRITY"
        )
    )

    requirement_ids = {
        row[0]
        for row in requirements
    }

    module_ids = {
        row[0]
        for row in modules
    }

    task_ids = {
        row[0]
        for row in tasks
    }

    task_requirement_counts = Counter(
        task[1]
        for task in tasks
    )

    missing_requirement_refs = [
        task[1]
        for task in tasks
        if task[1] not in requirement_ids
    ]

    missing_module_refs = [
        task[2]
        for task in tasks
        if task[2] not in module_ids
    ]

    duplicate_requirement_mappings = [
        rid
        for rid, count
        in task_requirement_counts.items()
        if count != 1
    ]

    requirements_without_tasks = [
        rid
        for rid in requirement_ids
        if task_requirement_counts[rid] == 0
    ]

    log(
        f"Missing requirement refs       : "
        f"{len(missing_requirement_refs)}"
    )

    log(
        f"Missing module refs            : "
        f"{len(missing_module_refs)}"
    )

    log(
        f"Duplicate requirement mappings : "
        f"{len(duplicate_requirement_mappings)}"
    )

    log(
        f"Requirements without tasks     : "
        f"{len(requirements_without_tasks)}"
    )

    # ============================================================
    # 8. ARCHITECTURE RELATION INTEGRITY
    # ============================================================

    log(
        section(
            "ARCHITECTURE RELATION INTEGRITY"
        )
    )

    relation_rows = db.execute(
        """
        SELECT
            source_module_id,
            target_module_id
        FROM architecture_relations
        WHERE project_id=?
        """,
        (PROJECT_ID,),
    ).fetchall()

    invalid_relations = [
        row
        for row in relation_rows
        if row[0] not in module_ids
        or row[1] not in module_ids
    ]

    log(
        f"Architecture relations : "
        f"{len(relation_rows)}"
    )

    log(
        f"Invalid relations      : "
        f"{len(invalid_relations)}"
    )

    # ============================================================
    # 9. TEST INTEGRITY
    # ============================================================

    log(
        section(
            "TEST INTEGRITY"
        )
    )

    test_rows = db.execute(
        """
        SELECT
            id,
            requirement_id,
            task_id
        FROM test_cases
        WHERE project_id=?
        ORDER BY id
        """,
        (PROJECT_ID,),
    ).fetchall()

    test_ids = {
        row[0]
        for row in test_rows
    }

    invalid_test_requirement_refs = [
        row
        for row in test_rows
        if row[1] is not None
        and row[1] not in requirement_ids
    ]

    invalid_test_task_refs = [
        row
        for row in test_rows
        if row[2] is not None
        and row[2] not in task_ids
    ]

    log(
        f"Test cases                     : "
        f"{len(test_rows)}"
    )

    log(
        f"Invalid test→requirement refs  : "
        f"{len(invalid_test_requirement_refs)}"
    )

    log(
        f"Invalid test→task refs         : "
        f"{len(invalid_test_task_refs)}"
    )

    # ============================================================
    # 10. TASK DEPENDENCY INTEGRITY
    # ============================================================

    log(
        section(
            "TASK DEPENDENCY INTEGRITY"
        )
    )

    dependency_rows = db.execute(
        """
        SELECT
            td.task_id,
            td.depends_on_task_id
        FROM task_dependencies td
        JOIN tasks t
          ON t.id = td.task_id
        WHERE t.project_id=?
        ORDER BY td.id
        """,
        (PROJECT_ID,),
    ).fetchall()

    invalid_dependency_refs = [
        row
        for row in dependency_rows
        if row[0] not in task_ids
        or row[1] not in task_ids
    ]

    log(
        f"Task dependencies            : "
        f"{len(dependency_rows)}"
    )

    log(
        f"Invalid dependency refs      : "
        f"{len(invalid_dependency_refs)}"
    )

    # ============================================================
    # 11. COMPLETE TRACEABILITY INTEGRITY
    # ============================================================

    log(
        section(
            "COMPLETE TRACEABILITY INTEGRITY"
        )
    )

    trace_rows = db.execute(
        """
        SELECT
            id,
            requirement_id,
            module_id,
            task_id,
            test_id
        FROM traceability_links
        WHERE project_id=?
        ORDER BY id
        """,
        (PROJECT_ID,),
    ).fetchall()

    invalid_trace_requirement_refs = [
        row
        for row in trace_rows
        if row[1] is not None
        and row[1] not in requirement_ids
    ]

    invalid_trace_module_refs = [
        row
        for row in trace_rows
        if row[2] is not None
        and row[2] not in module_ids
    ]

    invalid_trace_task_refs = [
        row
        for row in trace_rows
        if row[3] is not None
        and row[3] not in task_ids
    ]

    invalid_trace_test_refs = [
        row
        for row in trace_rows
        if row[4] is not None
        and row[4] not in test_ids
    ]

    log(
        f"Traceability links             : "
        f"{len(trace_rows)}"
    )

    log(
        f"Invalid trace→requirement refs : "
        f"{len(invalid_trace_requirement_refs)}"
    )

    log(
        f"Invalid trace→module refs      : "
        f"{len(invalid_trace_module_refs)}"
    )

    log(
        f"Invalid trace→task refs        : "
        f"{len(invalid_trace_task_refs)}"
    )

    log(
        f"Invalid trace→test refs        : "
        f"{len(invalid_trace_test_refs)}"
    )

    # ============================================================
    # 12. FINAL DECISION
    # ============================================================

    structural_pass = all(
        [
            # Core project counts
            project_counts["Requirements"] == 58,
            project_counts["Architecture Modules"] == 10,
            project_counts["Tasks"] == 58,
            project_counts["Test Cases"] == 58,

            # Oracle validation
            total == 58,
            len(oracle_missing) == 0,
            len(source_missing) == 0,
            len(predictions_missing) == 0,
            len(failures) == 0,

            # Task integrity
            len(missing_requirement_refs) == 0,
            len(missing_module_refs) == 0,
            len(duplicate_requirement_mappings) == 0,
            len(requirements_without_tasks) == 0,

            # Architecture integrity
            len(invalid_relations) == 0,

            # Test integrity
            len(invalid_test_requirement_refs) == 0,
            len(invalid_test_task_refs) == 0,

            # Dependency integrity
            len(invalid_dependency_refs) == 0,

            # Traceability integrity
            len(invalid_trace_requirement_refs) == 0,
            len(invalid_trace_module_refs) == 0,
            len(invalid_trace_task_refs) == 0,
            len(invalid_trace_test_refs) == 0,
        ]
    )

    log(
        section(
            "FINAL VALIDATION RESULT"
        )
    )

    if structural_pass:

        log("PASS")

        log()

        log(
            "ReqPilot achieved 100% agreement with the "
            "specification-derived deterministic validation "
            "oracle across all 58 EV requirements."
        )

        log()

        log(
            "All checked project-level structural integrity "
            "conditions also passed."
        )

    else:

        log("FAIL")

        log()

        log(
            "One or more reproducibility or structural "
            "checks failed."
        )

    db.close()

    # ============================================================
    # 13. SAVE REPORT
    # ============================================================

    REPORT_FILE.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print()

    print(
        "=" * 110
    )

    print(
        f"REPORT SAVED: {REPORT_FILE}"
    )

    print(
        "=" * 110
    )


if __name__ == "__main__":
    main()