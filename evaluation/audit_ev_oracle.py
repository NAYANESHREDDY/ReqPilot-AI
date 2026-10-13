import sqlite3
import re

DB = r".\backend\reqpilot.db"
PROJECT_ID = "ec691f0a-f7d3-4516-8f56-e834de9137ad"


# Same specification-derived oracle used by
# validate_ev_independent.py.
EXPECTED_MODULE = {

    "FR-001": "AUTHENTICATION",
    "FR-024": "AUTHENTICATION",
    "FR-026": "AUTHENTICATION",

    "FR-009": "CHARGING-STATION",
    "FR-010": "CHARGING-STATION",
    "FR-012": "CHARGING-STATION",
    "FR-013": "CHARGING-STATION",
    "FR-014": "CHARGING-STATION",
    "FR-025": "CHARGING-STATION",
    "FR-039": "CHARGING-STATION",
    "FR-047": "CHARGING-STATION",

    "FR-002": "BOOKING",
    "FR-011": "BOOKING",
    "FR-018": "BOOKING",
    "FR-027": "BOOKING",
    "FR-028": "BOOKING",
    "FR-029": "BOOKING",
    "FR-031": "BOOKING",
    "FR-040": "BOOKING",
    "FR-048": "BOOKING",

    "FR-003": "CHARGING-SESSION",
    "FR-004": "CHARGING-SESSION",
    "FR-007": "CHARGING-SESSION",
    "FR-030": "CHARGING-SESSION",
    "FR-041": "CHARGING-SESSION",

    "FR-005": "NOTIFICATION",
    "FR-006": "NOTIFICATION",
    "FR-023": "NOTIFICATION",
    "FR-032": "NOTIFICATION",
    "FR-033": "NOTIFICATION",
    "FR-034": "NOTIFICATION",
    "FR-042": "NOTIFICATION",

    "FR-008": "MAINTENANCE",
    "FR-015": "MAINTENANCE",
    "FR-016": "MAINTENANCE",
    "FR-017": "MAINTENANCE",
    "FR-020": "MAINTENANCE",

    "FR-019": "DATA",
    "FR-022": "DATA",
    "FR-045": "DATA",
    "FR-046": "DATA",
    "FR-051": "DATA",

    "FR-021": "REPORTING",
    "FR-043": "REPORTING",
    "FR-044": "REPORTING",
    "FR-049": "REPORTING",
    "FR-050": "REPORTING",

    "FR-035": "PAYMENT",
    "FR-036": "PAYMENT",
    "FR-037": "PAYMENT",
    "FR-038": "PAYMENT",

    "NFR-006": "GATEWAY",

    "NFR-001": "CHARGING-STATION",
    "NFR-002": "CHARGING-STATION",
    "NFR-003": "AUTHENTICATION",
    "NFR-004": "DATA",
    "NFR-005": "CHARGING-STATION",
    "NFR-007": "DATA",
}


DISPLAY_NAMES = {
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


def short_id(full_id):
    parts = full_id.split("-", 1)
    return parts[1] if len(parts) == 2 else full_id


def main():

    db = sqlite3.connect(DB)

    rows = db.execute(
        """
        SELECT
            r.id,
            r.req_type,
            r.summary,
            r.description,
            r.source_excerpt,
            r.source_page,
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

    print()
    print("=" * 120)
    print("EV SPECIFICATION-DERIVED ORACLE AUDIT")
    print("=" * 120)

    print(f"Requirements found: {len(rows)}")
    print(f"Oracle labels:      {len(EXPECTED_MODULE)}")

    missing_oracle = []
    missing_source = []

    for (
        rid,
        req_type,
        summary,
        description,
        source_excerpt,
        source_page,
        module_id,
    ) in rows:

        sid = short_id(rid)
        expected = EXPECTED_MODULE.get(sid)

        if expected is None:
            missing_oracle.append(sid)

        if not source_excerpt:
            missing_source.append(sid)

        print()
        print("-" * 120)
        print(f"{sid}")
        print(f"Type       : {req_type}")
        print(f"Source page: {source_page}")
        print(
            f"Oracle     : "
            f"{DISPLAY_NAMES.get(expected, expected)}"
        )
        print(f"Summary    : {summary}")
        print(f"Description: {description}")
        print(f"Source     : {source_excerpt}")

    print()
    print("=" * 120)
    print("ORACLE COVERAGE CHECK")
    print("=" * 120)

    print(f"Requirements in DB : {len(rows)}")
    print(f"Oracle entries     : {len(EXPECTED_MODULE)}")
    print(
        "Missing oracle labels:",
        missing_oracle if missing_oracle else "NONE"
    )
    print(
        "Missing source evidence:",
        missing_source if missing_source else "NONE"
    )

    if len(rows) == 58 and len(EXPECTED_MODULE) == 58:
        print()
        print("PASS: 58 requirements have specification-derived oracle labels.")
    else:
        print()
        print("FAIL: Oracle coverage is incomplete.")

    db.close()


if __name__ == "__main__":
    main()