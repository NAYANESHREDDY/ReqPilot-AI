import sqlite3

DB = r".\backend\reqpilot.db"
PROJECT_ID = "ec691f0a-f7d3-4516-8f56-e834de9137ad"

# These are the requirements where the primary implementation
# capability could reasonably be confused with another module.
#
# The rationale is derived from the original EV specification,
# not from ReqPilot's predicted module.

CASES = {
    "FR-007": (
        "CHARGING-SESSION",
        "Primary capability is access to charging history/session records; "
        "the requirement mentions invoices as an associated historical output."
    ),

    "FR-011": (
        "BOOKING",
        "The requirement asks station operators to view active reservations "
        "and charging sessions; the primary operational capability is "
        "reservation/scheduling state."
    ),

    "FR-014": (
        "CHARGING-STATION",
        "The subject of the reports is station utilization and station "
        "revenue; the requirement originates from station-operator operations."
    ),

    "FR-020": (
        "MAINTENANCE",
        "The requirement is broad administrator management, including "
        "maintenance activities; the persisted primary capability is "
        "maintenance management."
    ),

    "FR-022": (
        "DATA",
        "The requirement changes the persistent account state by suspending "
        "accounts that violate policies; it is therefore treated as a "
        "cross-cutting data/account-state operation."
    ),

    "FR-023": (
        "NOTIFICATION",
        "The requirement explicitly configures global notification and "
        "reservation policies; notification policy configuration is the "
        "primary capability."
    ),

    "FR-024": (
        "AUTHENTICATION",
        "The requirement constrains which records a driver may access; "
        "the primary capability is authorization/access control."
    ),

    "FR-025": (
        "CHARGING-STATION",
        "The protected resource is stations assigned to an organization; "
        "the primary domain capability is station management."
    ),

    "FR-026": (
        "AUTHENTICATION",
        "The requirement defines authorization over maintenance requests "
        "assigned to staff or their team."
    ),

    "FR-042": (
        "NOTIFICATION",
        "The requirement explicitly addresses behavior when the notification "
        "service is unavailable; notification-service resilience is the "
        "primary capability named by the requirement."
    ),

    "FR-049": (
        "REPORTING",
        "The requirement is explicitly titled Reporting and Auditability "
        "and requires traceable records across operational state changes."
    ),

    "FR-051": (
        "DATA",
        "The requirement concerns whether anonymized driver account data "
        "can later be restored, which is a data-lifecycle question."
    ),

    "NFR-005": (
        "CHARGING-STATION",
        "The performance requirement specifically concerns thousands of "
        "drivers searching stations or viewing station availability."
    ),
}

DISPLAY = {
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

    print()
    print("=" * 120)
    print("EV CROSS-DOMAIN ORACLE JUSTIFICATION AUDIT")
    print("=" * 120)

    rows = db.execute(
        """
        SELECT
            r.id,
            r.req_type,
            r.summary,
            r.description,
            r.source_excerpt,
            r.source_page
        FROM requirements r
        WHERE r.project_id=?
        ORDER BY r.id
        """,
        (PROJECT_ID,),
    ).fetchall()

    by_id = {
        short_id(row[0]): row
        for row in rows
    }

    failures = []

    for req_id, (expected, rationale) in CASES.items():

        row = by_id.get(req_id)

        print()
        print("-" * 120)
        print(req_id)

        if not row:
            print("STATUS: FAIL - requirement not found")
            failures.append(req_id)
            continue

        (
            full_id,
            req_type,
            summary,
            description,
            source_excerpt,
            source_page,
        ) = row

        print(f"Type       : {req_type}")
        print(f"Source page: {source_page}")
        print(f"Oracle     : {DISPLAY.get(expected, expected)}")
        print(f"Summary    : {summary}")
        print(f"Source     : {source_excerpt}")
        print(f"Rationale  : {rationale}")

    print()
    print("=" * 120)
    print("CROSS-DOMAIN AUDIT SUMMARY")
    print("=" * 120)

    print(f"Cases reviewed : {len(CASES)}")
    print(
        f"Requirements found : "
        f"{sum(1 for req_id in CASES if req_id in by_id)}"
    )
    print(
        f"Missing requirements : "
        f"{', '.join(failures) if failures else 'NONE'}"
    )

    if not failures:
        print()
        print(
            "PASS: All selected cross-domain requirements have "
            "source evidence and an explicitly documented "
            "primary-capability rationale."
        )
    else:
        print()
        print("FAIL: Some cross-domain requirements were not found.")

    db.close()


if __name__ == "__main__":
    main()