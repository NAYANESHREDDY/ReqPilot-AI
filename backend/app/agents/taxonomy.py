"""
ReqPilot AI — Unified Enterprise Architecture & Requirements Taxonomy
======================================================================
Defines canonical module IDs, display names, responsibilities, aliases,
and entity-to-capability mappings shared across ArchitectureAgent,
TaskDecompositionAgent, and evaluation harnesses.

Design Principles:
1. Zero circular imports: self-contained pure data structures and helper functions.
2. Canonical consistency: guarantees ArchitectureAgent and TaskDecompositionAgent
   share identical module IDs and capability boundaries.
3. Backward compatibility: preserves existing module IDs while eliminating duplicate
   or drift aliases (e.g., resolving MOD-APPOINTMENT -> MOD-BOOKING).
"""

from typing import Dict, List, Optional, Any, Set
import re

# ==============================================================================
# 1. CANONICAL MODULE DEFINITIONS
# ==============================================================================

CANONICAL_MODULES: Dict[str, Dict[str, Any]] = {
    "AUTHENTICATION": {
        "id": "MOD-AUTHENTICATION",
        "name": "Authentication & Authorization",
        "canonical_key": "AUTHENTICATION",
        "module_type": "service",
        "responsibilities": [
            "Register users and manage authentication credentials",
            "Authenticate users and issue authentication tokens/sessions",
            "Enforce authorization rules, role-based access control (RBAC), and staff permissions",
            "Enforce security policies, multi-factor authentication (MFA), and credential governance",
            "Enforce supervisory transaction overrides and compliance controls (e.g., PCI-DSS)",
        ],
        "aliases": [
            "auth", "authentication", "authorization", "security",
            "access control", "login", "credentials", "rbac", "permissions",
            "pci-dss", "compliance", "supervisory override", "identity",
        ],
    },
    "BOOKING": {
        "id": "MOD-BOOKING",
        "name": "Booking & Scheduling",
        "canonical_key": "BOOKING",
        "module_type": "service",
        "responsibilities": [
            "Create bookings, reservations, time slots, or appointment sessions",
            "Manage scheduling, appointment availability, and booking lifecycle",
            "Manage shopping cart, order placement, checkout process, and loan borrowing/renewal transactions",
            "Handle scheduling conflicts and time-slot availability locks",
        ],
        "aliases": [
            "booking", "bookings", "reservation", "reservations", "reserve",
            "appointment", "appointments", "schedul", "schedule", "scheduling",
            "cart", "shopping cart", "checkout", "order placement", "order",
            "borrow", "borrowing", "loan", "loans", "loan application", "circulation loan", "renewal",
        ],
    },
    "PAYMENT": {
        "id": "MOD-PAYMENT",
        "name": "Payment Management",
        "canonical_key": "PAYMENT",
        "module_type": "service",
        "responsibilities": [
            "Process financial payments, credit card transactions, and fund transfers",
            "Execute deposits, withdrawals, wire transfers, and billing settlements",
            "Track real-time transaction state, fee calculations, and refunds",
        ],
        "aliases": [
            "payment", "payments", "billing", "invoice", "invoices", "pay",
            "paid", "fund transfer", "wire transfer", "deposit", "withdrawal",
            "settlement", "refund", "transaction execution",
        ],
    },
    "NOTIFICATION": {
        "id": "MOD-NOTIFICATION",
        "name": "Notification Service",
        "canonical_key": "NOTIFICATION",
        "module_type": "service",
        "responsibilities": [
            "Generate and deliver notifications via email, SMS, or push alerts",
            "Deliver system alerts, critical threshold notifications, and customer status updates",
            "Manage user notification preferences and delivery logs",
        ],
        "aliases": [
            "notification", "notifications", "alert", "alerts", "email",
            "sms", "push notification", "message", "messaging",
        ],
    },
    "REPORTING": {
        "id": "MOD-REPORTING",
        "name": "Reporting & Analytics",
        "canonical_key": "REPORTING",
        "module_type": "service",
        "responsibilities": [
            "Generate analytical reports, summaries, audit logs, and business metrics",
            "Calculate aggregated statistics, operational summaries, and trend data",
            "Export reports in standard document formats (PDF, CSV, Excel)",
        ],
        "aliases": [
            "reporting", "reports", "report", "analytics", "statistics",
            "metrics", "summary report", "performance report",
        ],
    },
    "SEARCH": {
        "id": "MOD-SEARCH",
        "name": "Search & Discovery",
        "canonical_key": "SEARCH",
        "module_type": "service",
        "responsibilities": [
            "Search application entities, catalogs, books, or resources by keywords",
            "Apply filtering, sorting, faceted search, and query criteria",
            "Return search result listings matching user search queries",
        ],
        "aliases": [
            "search", "discovery", "lookup", "query", "filter", "filtering",
            "catalog search", "resource search",
        ],
    },
    "PROFILE": {
        "id": "MOD-PROFILE",
        "name": "Profile Management",
        "canonical_key": "PROFILE",
        "module_type": "service",
        "responsibilities": [
            "Manage user profile details, contact information, and personal settings",
            "Store customer preferences, saved addresses, and card settings",
            "Manage user reviews, ratings, wishlists, and account configuration",
        ],
        "aliases": [
            "profile", "profiles", "user profile", "user management",
            "preferences", "settings", "wishlist", "reviews",
        ],
    },
    "FILE": {
        "id": "MOD-FILE",
        "name": "File & Document Management",
        "canonical_key": "FILE",
        "module_type": "service",
        "responsibilities": [
            "Handle file uploads, document attachments, and binary storage",
            "Generate downloadable documents, packing slips, statements, and receipts",
            "Manage document metadata and secure download links",
        ],
        "aliases": [
            "file", "document", "upload", "download", "attachment",
            "packing slip", "statement download", "file storage",
        ],
    },
    "DATA": {
        "id": "MOD-DATA",
        "name": "Application Data Store",
        "canonical_key": "DATA",
        "module_type": "database",
        "responsibilities": [
            "Persist core entity records, master inventory balances, and item stocks",
            "Maintain financial ledger entries, balance states, interest calculations, and AML audit records",
            "Preserve historical records, audit logs, data retention, shelf location cataloging, and archival data",
        ],
        "aliases": [
            "data", "database", "datastore", "storage", "core storage",
            "inventory records", "stock","catalog", "cataloging", "collection management", "acquisition", "shelf location", "ledger",
            "balance state", "audit retention", "data persistence",
        ],
    },
    "GATEWAY": {
        "id": "MOD-GATEWAY",
        "name": "API Gateway",
        "canonical_key": "GATEWAY",
        "module_type": "gateway",
        "responsibilities": [
            "Route incoming API requests to internal application services",
            "Apply common request controls, rate limiting, and reverse proxy routing",
            "Ensure high availability and cross-cutting network resilience",
        ],
        "aliases": [
            "gateway", "api gateway", "proxy", "reverse proxy", "router",
        ],
    },
    # --------------------------------------------------------------------------
    # Specialized Domain Modules
    # --------------------------------------------------------------------------
    "CHARGING-STATION": {
        "id": "MOD-CHARGING-STATION",
        "name": "Charging Station Management",
        "canonical_key": "CHARGING-STATION",
        "module_type": "service",
        "responsibilities": [
            "Register, configure, and manage charging stations and physical chargers",
            "Manage charger operational states, connector specifications, and operating hours",
            "Control station/charger availability, disable chargers for maintenance, and track station utilization",
        ],
        "aliases": [
            "charging station", "charging stations", "station management",
            "charger", "chargers", "charging point", "charger availability",
        ],
    },
    "CHARGING-SESSION": {
        "id": "MOD-CHARGING-SESSION",
        "name": "Charging Session Management",
        "canonical_key": "CHARGING-SESSION",
        "module_type": "service",
        "responsibilities": [
            "Start, monitor, and stop charging sessions",
            "Track charging session telemetry, power metering, duration, and energy consumed (kWh)",
            "Record charging session history, session cost, and session invoices",
        ],
        "aliases": [
            "charging session", "charging sessions", "charging history",
            "energy consumed", "metering", "kwh", "session progress",
        ],
    },
    "MAINTENANCE": {
        "id": "MOD-MAINTENANCE",
        "name": "Maintenance Management",
        "canonical_key": "MAINTENANCE",
        "module_type": "service",
        "responsibilities": [
            "Track charger faults, equipment malfunctions, and maintenance requests",
            "Assign, schedule, and track maintenance work orders for technical staff",
            "Record equipment inspections, repair logs, and maintenance actions",
        ],
        "aliases": [
            "maintenance", "repairs", "fault report", "faults",
            "technician assignment", "work order", "equipment inspection",
        ],
    },
    "DEPARTMENT": {
        "id": "MOD-DOMAIN-DEPARTMENT",
        "name": "Department",
        "canonical_key": "DEPARTMENT",
        "module_type": "service",
        "responsibilities": [
            "Manage hospital/organization departments and clinical units",
            "Organize staff and administrative assignments by department",
        ],
        "aliases": [
            "department", "departments", "departmental", "clinical unit",
        ],
    },
}

# ==============================================================================
# 2. ENTITY TO CAPABILITY MAPPING (Used by ArchitectureAgent)
# ==============================================================================

# Prevents creation of redundant domain modules when a capability already covers them
ENTITY_TO_CAPABILITY: Dict[str, str] = {
    # Booking & Scheduling concepts
    "booking": "booking",
    "bookings": "booking",
    "appointment": "booking",
    "appointments": "booking",
    "appointment scheduling": "booking",
    "cart": "booking",
    "shopping cart": "booking",
    "order": "booking",
    "orders": "booking",
    "reservation": "booking",
    "reservations": "booking",
    "loan": "booking",
    "loans": "booking",
    "borrowing": "booking",

    # Search concepts
    "product catalog": "search",
    "catalog": "search",
    "search": "search",

    # Payment concepts
    "payment": "payment",
    "payments": "payment",
    "billing": "payment",
    "invoice": "payment",
    "invoices": "payment",

    # Notification concepts
    "notification": "notification",
    "notifications": "notification",
    "alert": "notification",
    "alerts": "notification",

    # Attendance
    "attendance": "attendance",
    "attendance record": "attendance",

    # Profile
    "user management": "profile",
    "profile": "profile",

    # EV concepts (ensures domain templates take precedence, no duplicate generic entities)
    "charging station": "charging_station",
    "charging stations": "charging_station",
    "charger": "charging_station",
    "chargers": "charging_station",
    "charging session": "charging_session",
    "charging sessions": "charging_session",
    "maintenance": "maintenance",
    "maintenance request": "maintenance",
    "maintenance requests": "maintenance",
}

# Synonyms mapped during entity discovery
ENTITY_ALIASES: Dict[str, str] = {
    "products": "product catalog",
    "product": "product catalog",
    "product catalog": "product catalog",
    "shopping cart": "cart",
    "carts": "cart",
    "orders": "order",
    "order": "order",
    "payments": "payment",
    "payment": "payment",
    "notifications": "notification",
    "notification": "notification",
    "attendance records": "attendance",
    "attendance record": "attendance",
    "attendance": "attendance",
    "users": "user management",
    "user": "user management",
    "students": "student management",
    "student": "student management",
    "faculty": "faculty management",
    "teachers": "faculty management",
    "teacher": "faculty management",
    # Crucial alias mappings:
    "appointment": "booking",
    "appointments": "booking",
    "appointment scheduling": "booking",
    "charging stations": "charging station",
    "charging sessions": "charging session",
    "maintenance requests": "maintenance",
}

# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================

def normalize_module_id(raw_id_or_name: str) -> Optional[str]:
    """
    Resolve any alias or raw identifier (e.g., 'MOD-APPOINTMENT', 'appointment',
    'MOD-BOOKING', 'Booking & Scheduling') to its canonical module ID.
    Returns None if unresolvable.
    """
    if not raw_id_or_name:
        return None
    cleaned = str(raw_id_or_name).strip()
    cleaned_upper = cleaned.upper()

    # Direct match on canonical IDs
    for mod_info in CANONICAL_MODULES.values():
        if cleaned_upper == mod_info["id"].upper():
            return mod_info["id"]
        if cleaned_upper.endswith(f"-{mod_info['id'].upper()}"):
            return mod_info["id"]

    # Match on canonical key
    for key, mod_info in CANONICAL_MODULES.items():
        if cleaned_upper == key or cleaned_upper == f"MOD-{key}":
            return mod_info["id"]

    # Match on display name or exact aliases
    clean_lower = cleaned.lower()
    clean_unprefixed = clean_lower.replace("mod-domain-", "").replace("mod-", "").strip().replace("-", " ")
    for mod_info in CANONICAL_MODULES.values():
        if clean_lower == mod_info["name"].lower():
            return mod_info["id"]
        for alias in mod_info["aliases"]:
            if (
                clean_lower == alias
                or clean_unprefixed == alias
                or clean_lower == f"mod-{alias}"
                or clean_lower == f"mod-{alias.replace(' ', '-')}"
            ):
                return mod_info["id"]

    if clean_unprefixed in ENTITY_ALIASES:
        target_cap = ENTITY_ALIASES[clean_unprefixed].upper()
        if target_cap in CANONICAL_MODULES:
            return CANONICAL_MODULES[target_cap]["id"]

    import difflib
    raw_key = cleaned_upper.replace("MOD-", "")
    canonical_keys = list(CANONICAL_MODULES.keys())
    close = difflib.get_close_matches(raw_key, canonical_keys, n=1, cutoff=0.8)
    if close:
        return CANONICAL_MODULES[close[0]]["id"]

    return None


def get_canonical_name(canonical_key_or_id: str) -> str:
    """Return the display name for a canonical key or ID."""
    for key, mod_info in CANONICAL_MODULES.items():
        if (
            canonical_key_or_id.upper() == key
            or canonical_key_or_id.upper() == mod_info["id"].upper()
        ):
            return mod_info["name"]
    return canonical_key_or_id

