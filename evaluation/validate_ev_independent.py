import sqlite3
from collections import Counter

DB = r".\backend\reqpilot.db"
PROJECT_ID = "ec691f0a-f7d3-4516-8f56-e834de9137ad"


# ============================================================
# INDEPENDENT SPECIFICATION-DERIVED ORACLE
# ============================================================
#
# IMPORTANT:
# The expected labels below are derived from the ORIGINAL EV
# requirements specification, independently of ReqPilot's
# predicted task/module assignments.
#
# We compare CANONICAL module IDs rather than display names.
#
# This avoids false mismatches such as:
#   Notification Service == Notifications & Communication
#   Application Data Store == Data Management
#   API Gateway == System Gateway
#
# The oracle defines the PRIMARY capability responsible for
# implementing each requirement.
# ============================================================


EXPECTED_MODULE = {

    # --------------------------------------------------------
    # Authentication & Authorization
    # --------------------------------------------------------
    "FR-001": "AUTHENTICATION",
    "FR-024": "AUTHENTICATION",
    "FR-026": "AUTHENTICATION",

    # --------------------------------------------------------
    # Charging Station Management
    # --------------------------------------------------------
    "FR-009": "CHARGING-STATION",
    "FR-010": "CHARGING-STATION",
    "FR-012": "CHARGING-STATION",
    "FR-013": "CHARGING-STATION",
    "FR-014": "CHARGING-STATION",
    "FR-025": "CHARGING-STATION",
    "FR-039": "CHARGING-STATION",
    "FR-047": "CHARGING-STATION",

    # --------------------------------------------------------
    # Booking & Scheduling
    # --------------------------------------------------------
    "FR-002": "BOOKING",
    "FR-011": "BOOKING",
    "FR-018": "BOOKING",
    "FR-027": "BOOKING",
    "FR-028": "BOOKING",
    "FR-029": "BOOKING",
    "FR-031": "BOOKING",
    "FR-040": "BOOKING",
    "FR-048": "BOOKING",

    # --------------------------------------------------------
    # Charging Session Management
    # --------------------------------------------------------
    "FR-003": "CHARGING-SESSION",
    "FR-004": "CHARGING-SESSION",
    "FR-007": "CHARGING-SESSION",
    "FR-030": "CHARGING-SESSION",
    "FR-041": "CHARGING-SESSION",

    # --------------------------------------------------------
    # Notification Service
    # --------------------------------------------------------
    "FR-005": "NOTIFICATION",
    "FR-006": "NOTIFICATION",
    "FR-023": "NOTIFICATION",
    "FR-032": "NOTIFICATION",
    "FR-033": "NOTIFICATION",
    "FR-034": "NOTIFICATION",
    "FR-042": "NOTIFICATION",

    # --------------------------------------------------------
    # Maintenance Management
    # --------------------------------------------------------
    "FR-008": "MAINTENANCE",
    "FR-015": "MAINTENANCE",
    "FR-016": "MAINTENANCE",
    "FR-017": "MAINTENANCE",
    "FR-020": "MAINTENANCE",

    # --------------------------------------------------------
    # Data Management
    # --------------------------------------------------------
    "FR-019": "DATA",
    "FR-022": "DATA",
    "FR-045": "DATA",
    "FR-046": "DATA",
    "FR-051": "DATA",

    # --------------------------------------------------------
    # Reporting & Analytics
    # --------------------------------------------------------
    "FR-021": "REPORTING",
    "FR-043": "REPORTING",
    "FR-044": "REPORTING",
    "FR-049": "REPORTING",
    "FR-050": "REPORTING",

    # --------------------------------------------------------
    # Payment Management
    # --------------------------------------------------------
    "FR-035": "PAYMENT",
    "FR-036": "PAYMENT",
    "FR-037": "PAYMENT",
    "FR-038": "PAYMENT",

    # --------------------------------------------------------
    # System Gateway
    # --------------------------------------------------------
    "NFR-006": "GATEWAY",

    # --------------------------------------------------------
    # Non-functional requirements
    # --------------------------------------------------------
    "NFR-001": "CHARGING-STATION",
    "NFR-002": "CHARGING-STATION",
    "NFR-003": "AUTHENTICATION",
    "NFR-004": "DATA",
    "NFR-005": "CHARGING-STATION",
    "NFR-007": "DATA",
}


# ============================================================
# CANONICALIZATION
# ============================================================

DISPLAY_TO_CANONICAL = {
    "Authentication & Authorization": "AUTHENTICATION",
    "Authentication": "AUTHENTICATION",

    "Charging Station Management": "CHARGING-STATION",

    "Booking & Scheduling": "BOOKING",

    "Charging Session Management": "CHARGING-SESSION",

    "Notification Service": "NOTIFICATION",
    "Notifications & Communication": "NOTIFICATION",

    "Maintenance Management": "MAINTENANCE",

    "Application Data Store": "DATA",
    "Data Management": "DATA",

    "Reporting & Analytics": "REPORTING",

    "Payment Management": "PAYMENT",

    "API Gateway": "GATEWAY",
    "System Gateway": "GATEWAY",
}


CANONICAL_TO_DISPLAY = {
    "AUTHENTICATION": "Authentication & Authorization",
    "CHARGING-STATION": "Charging Station Management",
    "BOOKING": "Booking & Scheduling",
    "CHARGING-SESSION": "Charging Session Management",
    "NOTIFICATION": "Notification Service",
    "MAINTENANCE": "Maintenance Management",
    "DATA": "Application Data Store",
    "REPORTING": "Reporting & Analytics",
    "PAYMENT": "Payment Management",
    "GATEWAY": "API Gateway",
}


# ============================================================
# HELPERS
# ============================================================

def short_requirement_id(full_id):
    """
    EC691F0A-FR-001 -> FR-001
    EC691F0A-NFR-001 -> NFR-001
    """
    if not full_id:
        return None

    parts = full_id.split("-", 1)
    return parts[1] if len(parts) == 2 else full_id


def canonicalize_module_name(name):
    if not name:
        return None

    return DISPLAY_TO_CANONICAL.get(name)


def get_module_name(db, module_id):
    if not module_id:
        return None

    row = db.execute(
        """
        SELECT name
        FROM architecture_modules
        WHERE id=? AND project_id=?
        """,
        (module_id, PROJECT_ID),
    ).fetchone()

    return row[0] if row else None


# ============================================================
# MAIN VALIDATION
# ============================================================

def main():

    db = sqlite3.connect(DB)

    rows = db.execute(
        """
        SELECT
            r.id,
            r.req_type,
            r.summary,
            r.description,
            t.module_id
        FROM requirements r
        LEFT JOIN tasks t
          ON t.requirement_id = r.id
         AND t.project_id = r.project_id
        WHERE r.project_id=?
        ORDER BY r.id
        """,
        (PROJECT_ID,),
    ).fetchall()

    results = []

    for rid, req_type, summary, description, predicted_module_id in rows:

        short_id = short_requirement_id(rid)

        expected = EXPECTED_MODULE.get(short_id)

        predicted_name = get_module_name(
            db,
            predicted_module_id
        )

        predicted = canonicalize_module_name(
            predicted_name
        )

        match = (
            expected is not None
            and predicted is not None
            and expected == predicted
        )

        results.append({
            "id": rid,
            "expected": expected,
            "predicted": predicted,
            "predicted_name": predicted_name,
            "match": match,
        })

    db.close()

    # ========================================================
    # BASIC COUNTS
    # ========================================================

    total = len(results)
    correct = sum(r["match"] for r in results)

    accuracy = (
        correct / total * 100
        if total
        else 0.0
    )

    print()
    print("=" * 110)
    print("INDEPENDENT EV VALIDATION")
    print("=" * 110)

    print(f"Requirements evaluated : {total}")
    print(f"Oracle labels defined  : {sum(1 for r in results if r['expected'])}")
    print(f"Correct classifications : {correct}")
    print(f"Accuracy               : {accuracy:.2f}%")

    # ========================================================
    # REQUIREMENT LEVEL RESULTS
    # ========================================================

    print()
    print("=" * 110)
    print("REQUIREMENT-LEVEL RESULTS")
    print("=" * 110)

    for r in results:

        status = "PASS" if r["match"] else "FAIL"

        expected_display = (
            CANONICAL_TO_DISPLAY.get(
                r["expected"],
                str(r["expected"])
            )
            if r["expected"]
            else "UNCLASSIFIED"
        )

        predicted_display = (
            CANONICAL_TO_DISPLAY.get(
                r["predicted"],
                str(r["predicted"])
            )
            if r["predicted"]
            else "MISSING"
        )

        print(
            f"{status:4} "
            f"{r['id']:22} "
            f"Expected={expected_display:<32} "
            f"ReqPilot={predicted_display}"
        )

    # ========================================================
    # FAILURES
    # ========================================================

    failures = [
        r for r in results
        if not r["match"]
    ]

    print()
    print("=" * 110)
    print("FAILURES")
    print("=" * 110)

    if not failures:
        print("NONE")
    else:
        for r in failures:
            print(
                f"{r['id']}: "
                f"expected={r['expected']}, "
                f"predicted={r['predicted']}, "
                f"ReqPilotName={r['predicted_name']}"
            )

    # ========================================================
    # PER-MODULE METRICS
    # ========================================================

    labels = sorted(
        set(
            r["expected"]
            for r in results
            if r["expected"]
        )
        |
        set(
            r["predicted"]
            for r in results
            if r["predicted"]
        )
    )

    print()
    print("=" * 110)
    print("PER-MODULE METRICS")
    print("=" * 110)

    print(
        f"{'MODULE':25}"
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
            for r in results
            if r["expected"] == label
            and r["predicted"] == label
        )

        fp = sum(
            1
            for r in results
            if r["expected"] != label
            and r["predicted"] == label
        )

        fn = sum(
            1
            for r in results
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
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )

        macro_precision.append(precision)
        macro_recall.append(recall)
        macro_f1.append(f1)

        print(
            f"{CANONICAL_TO_DISPLAY.get(label, label):25}"
            f"{tp:6}"
            f"{fp:6}"
            f"{fn:6}"
            f"{precision:12.3f}"
            f"{recall:10.3f}"
            f"{f1:10.3f}"
        )

    if labels:
        print()
        print(
            f"Macro Precision : "
            f"{sum(macro_precision) / len(labels):.3f}"
        )

        print(
            f"Macro Recall    : "
            f"{sum(macro_recall) / len(labels):.3f}"
        )

        print(
            f"Macro F1        : "
            f"{sum(macro_f1) / len(labels):.3f}"
        )

    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    print()
    print("=" * 110)
    print("CONFUSION MATRIX")
    print("=" * 110)

    matrix = Counter(
        (
            r["expected"],
            r["predicted"]
        )
        for r in results
        if r["expected"] and r["predicted"]
    )

    print(
        f"{'EXPECTED':25} -> PREDICTED"
    )

    for (expected, predicted), count in sorted(matrix.items()):

        if expected != predicted:
            print(
                f"{CANONICAL_TO_DISPLAY.get(expected, expected):25}"
                f" -> "
                f"{CANONICAL_TO_DISPLAY.get(predicted, predicted):25}"
                f" : {count}"
            )

    print()
    print("=" * 110)
    print("VALIDATION COMPLETE")
    print("=" * 110)


if __name__ == "__main__":
    main()