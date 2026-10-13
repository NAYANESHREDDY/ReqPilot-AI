from typing import List, Dict, Any, Optional, Set
import re
import logging

logger = logging.getLogger(__name__)


class ArchitectureAgent:
    """
    Requirement-driven deterministic architecture synthesis.

    Design goals:
    - Generate only architecture modules justified by requirements.
    - Prefer reusable application capabilities over raw domain nouns.
    - Avoid duplicate/overlapping modules.
    - Never turn generic target objects such as "account", "system",
      "user email", or "dashboard" into unnecessary services.
    - Keep architecture relationships conservative and evidence-driven.
    - Preserve the existing workflow contract:
          generate_architecture(requirements, project_title)
        ->
          {
              "modules": [...],
              "relations": [...]
          }
    """

    # ------------------------------------------------------------------
    # Capability rules
    # ------------------------------------------------------------------
    #
    # IMPORTANT:
    # dashboard is intentionally NOT a reporting signal.
    # An explicit dashboard requirement maps to a Dashboard/Presentation
    # capability rather than Reporting & Analytics.
    #
    CAPABILITY_RULES = [
        {
            "key": "authentication",
            "patterns": [
                r"\blog[\s-]*in\b",
                r"\blog[\s-]*out\b",
                r"\bsign[\s-]*in\b",
                r"\bsign[\s-]*up\b",
                r"\bauthenticat\w*\b",
                r"\bauthoriz\w*\b",
                r"\bcredentials?\b",
                r"\bpassword\w*\b",
                r"\baccess control\b",
                r"\brole[- ]based access\b",
                r"\bpermission\w*\b",
                r"\bregister\w*\b",
                r"\bverification\b",
                r"\bverified user\b",
                r"\bsession\w*\b",
            ],
            "name": "Authentication & Authorization",
            "responsibilities": [
                "Register users and manage authentication credentials",
                "Authenticate users",
                "Validate credentials",
                "Enforce authorization rules",
                "Manage authenticated sessions",
            ],
            "endpoints": [
                "/api/auth/register",
                "/api/auth/login",
                "/api/auth/verify",
                "/api/auth/logout",
            ],
        },
        {
            "key": "profile",
            "patterns": [
                r"\bprofile\b",
                r"\bprofiles\b",
                r"\bprofile information\b",
                r"\bprofile picture\b",
                r"\bdisplay name\b",
                r"\bpersonal information\b",
                r"\buser details\b",
                r"\baccount information\b",
                r"\bdebit card\b",
                r"\bcredit card\b",
                r"\bcard activation\b",
                r"\bwishlist\b",
            ],
            "name": "Profile Management",
            "responsibilities": [
                "Retrieve user profile information",
                "Update profile attributes",
                "Manage user preferences",
            ],
            "endpoints": [
                "/api/users/profile",
                "/api/users/profile/{id}",
            ],
        },
        {
            "key": "notification",
            "patterns": [
                r"\bnotif\w*\b",
                r"\balert\w*\b",
                r"\bremind\w*\b",
                r"\bverification email\b",
                r"\bverification link\b",
                r"\bconfirmation email\b",
                r"\bemail notification\b",
                r"\bemail-based\b",
                r"\bnotification preferences\b",
                r"\bsms\b",
                r"\bpush notification\b",
            ],
            "name": "Notification Service",
            "responsibilities": [
                "Generate application notifications",
                "Deliver email or other supported notifications",
                "Manage notification preferences when required",
            ],
            "endpoints": [
                "/api/notifications",
                "/api/notifications/preferences",
            ],
        },
        {
            "key": "dashboard",
            "patterns": [
                r"\bdashboard\b",
                r"\bhome screen\b",
                r"\bsummary screen\b",
                r"\boverview screen\b",
            ],
            "name": "Dashboard",
            "responsibilities": [
                "Present authenticated user information",
                "Display recent activity or relevant summaries",
                "Provide the application dashboard experience",
            ],
            "endpoints": [
                "/api/dashboard",
            ],
        },
        {
            "key": "reporting",
            "patterns": [
                r"\breport\w*\b",
                r"\banalytics\b",
                r"\banaly[sz]\w*\b",
                r"\bstatistics\b",
                r"\bmetrics\b",
                r"\bperformance report\b",
                r"\bsummary report\b",
                r"\btax invoices?\b",
                r"\bitemized receipts?\b",
            ],
            "name": "Reporting & Analytics",
            "responsibilities": [
                "Generate explicitly requested reports",
                "Calculate explicitly requested metrics",
                "Expose analytical information required by the system",
            ],
            "endpoints": [
                "/api/reports",
                "/api/reports/{id}",
            ],
        },
        {
            "key": "search",
            "patterns": [
                r"\bsearch\b",
                r"\bsearchable\b",
                r"\bfilter\w*\b",
                r"\bquery\b",
                r"\bfind\b",
                r"\bdiscover\w*\b",
                r"\blook up\b",
            ],
            "name": "Search & Discovery",
            "responsibilities": [
                "Search application data",
                "Apply filtering or query criteria",
                "Return matching results",
            ],
            "endpoints": [
                "/api/search",
                "/api/search/{query}",
            ],
        },
        {
            "key": "payment",
            "patterns": [
                r"\bpayment\w*\b",
                r"\bpay\b",
                r"\bpaid\b",
                r"\btransaction\w*\b",
                r"\brefund\w*\b",
                r"\bbilling\b",
                r"\binvoice\w*\b",
            ],
            "name": "Payment Management",
            "responsibilities": [
                "Process payments",
                "Track transaction state",
                "Handle payment-related operations",
            ],
            "endpoints": [
                "/api/payments",
                "/api/payments/{id}",
            ],
        },
        {
            "key": "booking",
            "patterns": [
                r"\bbook\w*\b",
                r"\breserv\w*\b",
                r"\bappointment\b",
                r"\bschedul\w*\b",
                r"\bshopping cart\b",
                r"\bcart\b",
                r"\badd to cart\b",
                r"\bremove from cart\b",
                r"\bcheckout\b",
                r"\border\w*\b",
                r"\b(?!purchase\s+recommendation)purchase\w*\b",
            ],
            "name": "Booking & Scheduling",
            "responsibilities": [
                "Create bookings, reservations, or transaction sessions",
                "Manage scheduling and checkout state",
                "Handle scheduling conflicts",
            ],
            "endpoints": [
                "/api/bookings",
                "/api/bookings/{id}",
            ],
        },
        {
            "key": "attendance",
            "patterns": [
                r"\battendance\b",
                r"\babsent\b",
                r"\babsence\b",
                r"\bpresent\b",
                r"\battendance percentage\b",
                r"\battendance record\b",
            ],
            "name": "Attendance Management",
            "responsibilities": [
                "Record attendance",
                "Retrieve attendance records",
                "Calculate attendance status or percentage",
            ],
            "endpoints": [
                "/api/attendance",
                "/api/attendance/{id}",
            ],
        },
        {
            "key": "file",
            "patterns": [
                r"\bupload\w*\b",
                r"\bdownload\w*\b",
                r"\battachment\w*\b",
                r"\bfile management\b",
                r"\bdocument management\b",
                r"\bpacking slips?\b",
            ],
            "name": "File & Document Management",
            "responsibilities": [
                "Upload application files",
                "Retrieve stored files",
                "Manage document metadata",
            ],
            "endpoints": [
                "/api/files",
                "/api/files/{id}",
            ],
        },
        {
            "key": "charging_station",
            "patterns": [
                r"\bcharging station\w*\b",
                r"\bstation operator\w*\b",
                r"\bconnector type\w*\b",
                r"\bcharging speed\w*\b",
                r"\bstation-specific pricing\b",
                r"\bstation utilization\b",
                r"\bcharger identifier\w*\b",
                r"\bcharger availability\b",
                r"\bcharger operating hour\w*\b",
                r"\bcharging station registration\b",
                r"\bmanage charging station\w*\b",
                r"\bregister charging station\w*\b",
            ],
            "name": "Charging Station Management",
            "responsibilities": [
                "Register and manage charging stations",
                "Configure charger identifiers, connectors, speeds, and operating hours",
                "Manage charger availability and station operational state",
                "Support station-level configuration and utilization",
            ],
            "endpoints": [
                "/api/stations",
                "/api/stations/{id}",
                "/api/chargers",
                "/api/chargers/{id}",
            ],
        },
        {
            "key": "charging_session",
            "patterns": [
                r"\bcharging session\w*\b",
                r"\bstart charging\b",
                r"\bcharging session status\b",
                r"\benergy consumed\b",
                r"\bcharging history\b",
                r"\bcharging-session state\b",
            ],
            "name": "Charging Session Management",
            "responsibilities": [
                "Start and manage charging sessions",
                "Track charging session state and progress",
                "Record energy consumption, duration, and charging cost",
                "Recover charging session state when required",
            ],
            "endpoints": [
                "/api/charging-sessions",
                "/api/charging-sessions/{id}",
            ],
        },
        {
            "key": "maintenance",
            "patterns": [
                r"\bmaintenance request\w*\b",
                r"\bmaintenance staff\b",
                r"\bmaintenance assignment\w*\b",
                r"\bcharger fault\w*\b",
                r"\bfaulty charger\w*\b",
                r"\brepair action\w*\b",
                r"\binspection result\w*\b",
                r"\bmaintenance schedule\w*\b",
                r"\bcharger maintenance\b",
                r"\bdisable.*maintenance\b",
                r"\bmaintenance.*charger\b",
                r"\bmaintenance.*station\b",
            ],
            "name": "Maintenance Management",
            "responsibilities": [
                "Manage charger faults and maintenance requests",
                "Assign and track maintenance work",
                "Record inspections and repair actions",
                "Control charger availability during maintenance",
            ],
            "endpoints": [
                "/api/maintenance",
                "/api/maintenance/{id}",
                "/api/maintenance/faults",
            ],
        },
    ]

    # ------------------------------------------------------------------
    # Generic terms that must NEVER become standalone modules.
    # ------------------------------------------------------------------

    NON_MODULE_ENTITIES = {
        "account",
        "accounts",
        "system",
        "application",
        "software",
        "platform",
        "component",
        "components",
        "service",
        "services",
        "operation",
        "operations",
        "request",
        "requests",
        "response",
        "responses",
        "result",
        "results",
        "data",
        "information",
        "record",
        "records",
        "user",
        "users",
        "customer",
        "customers",
        "email",
        "user email",
        "password",
        "credential",
        "credentials",
        "session",
        "sessions",
    }

    STOPWORDS = {
        "the",
        "a",
        "an",
        "their",
        "his",
        "her",
        "our",
        "your",
        "this",
        "that",
        "these",
        "those",
        "for",
        "from",
        "with",
        "without",
        "into",
        "onto",
        "over",
        "under",
        "within",
        "between",
        "among",
        "using",
        "through",
        "by",
        "in",
        "on",
        "at",
        "to",
        "of",
        "and",
        "or",
        "are",
        "is",
        "was",
        "were",
        "be",
        "been",
        "being",
        "shall",
        "should",
        "can",
        "could",
        "will",
        "would",
        "may",
        "might",
        "must",
        "matching",
        "successfully",
        "success",
        "system",
        "application",
        "software",
        "platform",
        "service",
        "services",
        "user",
        "users",
        "customer",
        "customers",
        "person",
        "people",
        "data",
        "information",
        "record",
        "records",
        "result",
        "results",
        "request",
        "requests",
        "response",
        "responses",
        "operation",
        "operations",
        "feature",
        "features",
        "requirement",
        "requirements",
        "component",
        "components",
        "module",
        "modules",
        "function",
        "functions",
        "capability",
        "capabilities",
        "mechanism",
        "mechanisms",
    }

    # Existing aliases are retained for compatibility with other domains.
    ENTITY_ALIASES = {
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
        "appointment": "booking",
        "appointments": "booking",
        "appointment scheduling": "booking",
        "charging stations": "charging station",
        "charging sessions": "charging session",
        "maintenance requests": "maintenance",
    }

    KNOWN_CAPABILITY_KEYS = {
        rule["key"] for rule in CAPABILITY_RULES
    }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm

    async def generate_architecture_semantic(
        self,
        requirements: List[Dict[str, Any]],
        project_title: str,
    ) -> Dict[str, Any]:
        """
        Generate system architecture using semantic LLM analysis when available,
        with strict validation against architecture quality rules and automatic
        fallback to the deterministic engine.
        """
        if not self.llm or not getattr(self.llm, "api_key", "") or not requirements:
            logger.info("LLM not configured or requirements empty; using deterministic architecture synthesis.")
            return self.generate_architecture(requirements, project_title)

        try:
            req_summaries = []
            valid_req_ids = set()
            for r in requirements:
                rid = str(r.get("id") or "").strip()
                if not rid:
                    continue
                valid_req_ids.add(rid)
                sum_text = str(r.get("summary") or r.get("description") or "").strip()
                actor = str(r.get("actor") or "").strip()
                action = str(r.get("action") or "").strip()
                target = str(r.get("target_object") or "").strip()
                req_summaries.append(f"- ID: {rid} | Summary: {sum_text} | Actor: {actor} | Action: {action} | Target: {target}")

            reqs_text = "\n".join(req_summaries[:80])

            prompt = f"""You are ReqPilot AI, an expert enterprise software architect.
Analyze the following software requirements for project "{project_title}" and propose a clean, decoupled microservices/service-oriented application architecture.

============================================================
SOFTWARE REQUIREMENTS ({len(req_summaries)} items)
============================================================
{reqs_text}

============================================================
ARCHITECTURE DESIGN RULES
============================================================
1. Propose 5 to 10 cohesive application service modules justified directly by the requirements.
   - If requirements mention equipment faults, work orders, repairs, or maintenance: you MUST include MOD-MAINTENANCE.
   - If requirements mention generating reports, metrics, or operational analytics: you MUST include MOD-REPORTING.
   - Include MOD-FILE for document uploads/packing slips.
2. MODULE IDS: Must follow the convention 'MOD-<CAPABILITY_SLUG>' in uppercase.
   Prefer standard enterprise capability modules when applicable:
   - MOD-AUTHENTICATION (Authentication & Authorization)
   - MOD-BOOKING (Booking & Scheduling, appointments, reservations, checkout/cart, loans)
   - MOD-PAYMENT (Payment Management, billing, invoices, fees, fund transfers)
   - MOD-NOTIFICATION (Notification Service, email, SMS, push alerts)
   - MOD-REPORTING (Reporting & Analytics, metrics, summaries, statistics)
   - MOD-SEARCH (Search & Discovery, lookup, queries, filters; note: do NOT create for physical charging networks where station discovery belongs to Charging Station Management)
   - MOD-PROFILE (Profile Management, customer accounts, settings, wishlists)
   - MOD-FILE (File & Document Management, statements, uploads/downloads)
   - MOD-CHARGING-STATION (Charging Station Management: stations, chargers, availability, pricing)
   - MOD-CHARGING-SESSION (Charging Session Management: telemetry, metering, sessions)
   - MOD-MAINTENANCE (Maintenance Management: faults, work orders, repairs, inspections)
   - Or appropriate domain-specific functional capability modules derived directly from the project's unique business domain (e.g. specialized domain workflows, domain asset managers, or operational engines) when supported by direct requirement evidence.
3. EVIDENCE: Each proposed module MUST cite at least 1-2 requirement IDs that justify its existence in 'evidence_requirement_ids'.
4. NO TRIVIAL NOUNS: Do NOT create separate modules for generic non-service nouns such as "account", "system", "user email", "screen", "page", or "dashboard".
5. DO NOT include database/persistence in the services list: master inventory records, catalog entity storage, stock balances, ledgers, and database persistence belong to the centralized Application Data Store (MOD-DATA), which will be automatically attached.
6. DO NOT include API gateway in the services list (MOD-GATEWAY will be automatically attached if 2+ services exist).
7. For each module provide:
   - id: 'MOD-<SLUG>'
   - name: Clear Title Case Name (e.g. 'Fleet & Vehicle Management')
   - description: 1-2 sentence engineering description
   - responsibilities: List of 2-5 distinct responsibilities
   - evidence_requirement_ids: List of requirement IDs directly implemented by this module
8. For relations, propose direct functional dependencies between services (e.g. relation_type 'calls', 'publishes_to', 'reads_from').
"""

            schema = """{
  "modules": [
    {
      "id": "MOD-AUTHENTICATION",
      "name": "Authentication & Authorization",
      "description": "Handles user credentials, tokens, and role-based permissions.",
      "responsibilities": ["Authenticate users", "Enforce RBAC"],
      "evidence_requirement_ids": ["FR-001", "FR-002"]
    }
  ],
  "relations": [
    {
      "source_module_id": "MOD-BOOKING",
      "target_module_id": "MOD-NOTIFICATION",
      "relation_type": "publishes_to",
      "description": "Booking service publishes status events to notification service."
    }
  ]
}"""

            response = await self.llm.generate_json(prompt, schema)
            if not response or not isinstance(response, dict):
                logger.warning("Semantic architecture synthesis returned non-dict response. Falling back to deterministic engine.")
                return self.generate_architecture(requirements, project_title)

            raw_modules = response.get("modules")
            if not isinstance(raw_modules, list) or len(raw_modules) < 2:
                logger.warning("Semantic architecture synthesis returned fewer than 2 modules. Falling back to deterministic engine.")
                return self.generate_architecture(requirements, project_title)

            # Validate and synthesize validated modules
            validated_modules: List[Dict[str, Any]] = []
            seen_ids = set()

            for raw_m in raw_modules:
                if not isinstance(raw_m, dict):
                    continue
                raw_id = str(raw_m.get("id") or "").strip().upper()
                raw_name = str(raw_m.get("name") or "").strip()
                raw_desc = str(raw_m.get("description") or "").strip()
                responsibilities = raw_m.get("responsibilities", [])
                evidence = [str(eid).strip() for eid in raw_m.get("evidence_requirement_ids", []) if str(eid).strip() in valid_req_ids]

                if not raw_id.startswith("MOD-"):
                    raw_id = f"MOD-{re.sub(r'[^A-Z0-9]+', '-', raw_id).strip('-')}"

                # Ignore generic / persistence / gateway from LLM output (we handle those deterministically)
                if raw_id in {"MOD-DATA", "MOD-GATEWAY", "MOD-DATABASE", "MOD-API-GATEWAY", "MOD-SYSTEM", "MOD-DASHBOARD"}:
                    continue

                # Core financial transactions map to Payment Management capability
                if raw_id in {"MOD-TRANSACTION", "MOD-TRANSACTIONS", "MOD-CORE-TRANSACTION", "MOD-TRANSACTION-PROCESSING"}:
                    raw_id = "MOD-PAYMENT"

                if raw_id in seen_ids:
                    continue

                # Align canonical names if raw_id matches a known canonical capability
                from backend.app.agents.taxonomy import CANONICAL_MODULES, normalize_module_id
                canon_id = normalize_module_id(raw_id)
                if canon_id:
                    for c_info in CANONICAL_MODULES.values():
                        if c_info["id"] == canon_id:
                            raw_name = c_info["name"]
                            raw_id = c_info["id"]
                            break
                if raw_id in seen_ids:
                    continue
                elif not raw_name:
                    raw_name = self._title_case(raw_id.replace("MOD-", "").replace("-", " ").lower())

                slug = raw_id.replace("MOD-", "").lower()
                endpoints = [f"/api/{slug}", f"/api/{slug}/{{id}}"]

                if not isinstance(responsibilities, list) or not responsibilities:
                    responsibilities = [f"Manage {raw_name} capabilities", f"Provide operations for {raw_name}"]

                validated_modules.append({
                    "id": raw_id,
                    "name": raw_name,
                    "description": raw_desc or f"Provides {raw_name} capabilities derived from requirements.",
                    "module_type": "service",
                    "tech_stack": "Application API + relational data access",
                    "responsibilities": [str(r) for r in responsibilities[:6]],
                    "api_endpoints": endpoints,
                    "pos_x": 150.0,
                    "pos_y": 180.0,
                    "is_ai_suggested": True,
                    "status": "approved",
                })
                seen_ids.add(raw_id)

            if len(validated_modules) < 2:
                logger.warning("Fewer than 2 valid service modules after validation. Falling back to deterministic engine.")
                return self.generate_architecture(requirements, project_title)

            # Defensive architecture completeness: If requirements explicitly demand reporting / analytics and LLM omitted it
            if "MOD-REPORTING" not in seen_ids:
                normalized = self._normalize_requirements(requirements)
                has_rep = any(
                    re.search(r"\b(generate|producing|view|viewing)\s+([a-z\s]+)?reports?\b", r["text"], re.I)
                    for r in normalized
                    if not self._is_operational_fault_reporting(r["text"])
                )
                if has_rep:
                    validated_modules.append({
                        "id": "MOD-REPORTING",
                        "name": "Reporting & Analytics",
                        "description": "Generates business intelligence, operational metrics, and domain summary reports.",
                        "module_type": "service",
                        "tech_stack": "Application API + analytics processing",
                        "responsibilities": ["Generate operational reports", "Provide analytical aggregations"],
                        "api_endpoints": ["/api/reporting", "/api/reporting/{id}"],
                        "pos_x": 150.0,
                        "pos_y": 180.0,
                        "is_ai_suggested": True,
                        "status": "approved",
                    })
                    seen_ids.add("MOD-REPORTING")

            # Add Data Module (persistence boundary)
            validated_modules.append(self._build_data_module())

            # Add API Gateway if 2 or more services exist
            gateway_id = None
            if len(validated_modules) >= 2:
                gateway_id = "MOD-GATEWAY"
                validated_modules.insert(
                    0,
                    {
                        "id": gateway_id,
                        "name": "API Gateway",
                        "description": (
                            "Provides a common entry point for the "
                            "application services derived from the "
                            "software requirements."
                        ),
                        "module_type": "gateway",
                        "tech_stack": "API gateway / reverse proxy",
                        "responsibilities": [
                            "Route API requests",
                            "Apply common request controls",
                        ],
                        "api_endpoints": ["/api/*"],
                        "pos_x": 400.0,
                        "pos_y": 50.0,
                        "is_ai_suggested": True,
                        "status": "approved",
                    },
                )

            # Assign 2D layout positions
            self._assign_positions(validated_modules)

            # Validate relations
            valid_module_ids = {m["id"] for m in validated_modules}
            validated_relations = []
            seen_rel_keys = set()

            # Gateway -> services relations
            if gateway_id:
                for s in validated_modules:
                    if s["module_type"] == "service":
                        key = (gateway_id, s["id"], "routes_to")
                        seen_rel_keys.add(key)
                        validated_relations.append({
                            "source_module_id": gateway_id,
                            "target_module_id": s["id"],
                            "relation_type": "routes_to",
                            "description": "Gateway routes external requests to this service.",
                        })

            # Services -> data relations
            for s in validated_modules:
                if s["module_type"] == "service":
                    key = (s["id"], "MOD-DATA", "persists_to")
                    seen_rel_keys.add(key)
                    validated_relations.append({
                        "source_module_id": s["id"],
                        "target_module_id": "MOD-DATA",
                        "relation_type": "persists_to",
                        "description": f"{s['name']} persists state to application data store.",
                    })

            # Process LLM proposed service-to-service relations
            raw_relations = response.get("relations", [])
            if isinstance(raw_relations, list):
                for rel in raw_relations:
                    if not isinstance(rel, dict):
                        continue
                    src = str(rel.get("source_module_id") or "").strip().upper()
                    tgt = str(rel.get("target_module_id") or "").strip().upper()
                    rtype = str(rel.get("relation_type") or "calls").strip().lower()
                    rdesc = str(rel.get("description") or f"{src} connects to {tgt}").strip()

                    if src in valid_module_ids and tgt in valid_module_ids and src != tgt:
                        key = (src, tgt, rtype)
                        if key not in seen_rel_keys:
                            seen_rel_keys.add(key)
                            validated_relations.append({
                                "source_module_id": src,
                                "target_module_id": tgt,
                                "relation_type": rtype,
                                "description": rdesc,
                            })

            logger.info("Successfully synthesized semantic architecture with %d modules and %d relations.", len(validated_modules), len(validated_relations))
            return {
                "modules": validated_modules,
                "relations": validated_relations,
            }

        except Exception as e:
            logger.warning("Error during semantic architecture generation: %s. Falling back to deterministic engine.", e)
            return self.generate_architecture(requirements, project_title)

    def generate_architecture(
        self,
        requirements: List[Dict[str, Any]],
        project_title: str,
    ) -> Dict[str, Any]:
        """
        Generate a compact architecture from structured requirements.

        Quality policy:
        - A module must have direct textual evidence.
        - Generic entities do not become modules.
        - Overlapping capabilities are merged.
        - Persistence is represented once.
        - Relationships are generated only for justified dependencies.
        """

        normalized = self._normalize_requirements(requirements)

        modules: List[Dict[str, Any]] = []
        used_capabilities: Set[str] = set()

        # --------------------------------------------------------------
        # 1. Detect explicit/reusable capabilities.
        # --------------------------------------------------------------

        for rule in self.CAPABILITY_RULES:
            matches = self._matching_requirements(
                normalized,
                rule["patterns"],
            )

            if not matches:
                continue

            # Reporting must exclude operational fault-reporting events.
            # Example:
            #   "generate reports" -> Reporting
            #   "report a faulty charger" -> Maintenance
            #   "charger reports a critical fault" -> Maintenance/Notification
            if rule["key"] == "reporting":
                matches = [
                    match
                    for match in matches
                    if not self._is_operational_fault_reporting(
                        match["text"]
                    )
                ]

                if not matches:
                    continue

                if not self._has_explicit_reporting_requirement(matches):
                    continue

            modules.append(
                self._build_rule_module(
                    rule,
                    matches,
                )
            )
            used_capabilities.add(rule["key"])

        # --------------------------------------------------------------
        # 2. Very conservative domain discovery.
        #
        # We only create a domain module when:
        #   - the entity is meaningful,
        #   - it is not already represented by a capability,
        #   - it appears in at least TWO requirements, OR
        #   - it is explicitly a domain noun in multiple structured fields.
        #
        # This prevents Account/Profile/Dashboard/User Email explosion.
        # --------------------------------------------------------------

        generic_candidates = self._discover_domain_entities(
            normalized,
            used_capabilities,
        )

        for candidate in generic_candidates:
            modules.append(
                self._build_domain_module(candidate)
            )

        # --------------------------------------------------------------
        # 3. Always provide one persistence boundary.
        # --------------------------------------------------------------

        modules.append(
            self._build_data_module()
        )

        # --------------------------------------------------------------
        # 4. Gateway only when there are multiple meaningful services.
        # --------------------------------------------------------------

        services = [
            module
            for module in modules
            if module["module_type"] == "service"
        ]

        gateway_id: Optional[str] = None

        if len(services) >= 2:
            gateway_id = "MOD-GATEWAY"

            modules.insert(
                0,
                {
                    "id": gateway_id,
                    "name": "API Gateway",
                    "description": (
                        "Provides a common entry point for the "
                        "application services derived from the "
                        "software requirements."
                    ),
                    "module_type": "gateway",
                    "tech_stack": "API gateway / reverse proxy",
                    "responsibilities": [
                        "Route API requests",
                        "Apply common request controls",
                    ],
                    "api_endpoints": ["/api/*"],
                    "pos_x": 400.0,
                    "pos_y": 50.0,
                    "is_ai_suggested": True,
                    "status": "approved",
                },
            )

        # --------------------------------------------------------------
        # 5. Layout.
        # --------------------------------------------------------------

        self._assign_positions(modules)

        # --------------------------------------------------------------
        # 6. Evidence-based relations.
        # --------------------------------------------------------------

        relations = self._generate_relations(
            modules,
            gateway_id,
            normalized,
        )

        return {
            "modules": modules,
            "relations": relations,
        }

    # ==================================================================
    # Normalization
    # ==================================================================

    @staticmethod
    def _normalize_requirements(
        requirements: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result = []

        for req in requirements:
            fields = [
                req.get("summary"),
                req.get("description"),
                req.get("actor"),
                req.get("action"),
                req.get("target_object"),
                req.get("preconditions"),
                req.get("expected_outcome"),
                req.get("acceptance_criteria"),
            ]

            text = " ".join(
                str(value)
                for value in fields
                if value is not None
            )

            text = re.sub(r"\s+", " ", text).strip()

            result.append(
                {
                    "id": req.get("id"),
                    "req_type": req.get("req_type"),
                    "text": text,
                    "original": req,
                }
            )

        return result

    
    def _matching_requirements(
    self,
    requirements: List[Dict[str, Any]],
    patterns: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Match requirements to architecture capabilities while keeping
        functional capability evidence separate from purely non-functional
        constraints.

        Functional requirements are the primary evidence for service/module
        boundaries. Non-functional requirements may still support an existing
        capability boundary, but they should not by themselves create a
        functional service module.
        """
        matches = []

        for req in requirements:
            req_type = str(req.get("req_type", "")).strip().lower()

            text = str(req.get("text", ""))
            if not text:
                continue

            if not any(
                re.search(pattern, text, re.IGNORECASE)
                for pattern in patterns
            ):
                continue

            # Functional requirements are always eligible as capability evidence.
            if req_type in {"functional", "fr"}:
                matches.append(req)
                continue

            # Non-functional requirements can describe constraints on an
            # already-existing capability, but should not independently define
            # a functional service boundary, unless they explicitly require dedicated
            # communication/delivery mechanisms (e.g. SMS, push notifications, alerts).
            if req_type in {"non_functional", "nfr"}:
                if any(re.search(p, text, re.IGNORECASE) for p in [r"\bsms\b", r"\bpush notification\w*\b", r"\bemail notification\w*\b"]):
                    matches.append(req)
                continue

            # Preserve compatibility with older/unknown requirement records.
            # If type information is absent, retain the previous behavior.
            if not req_type:
                matches.append(req)

        return matches

    @staticmethod
    def _is_operational_fault_reporting(text: str) -> bool:
        """
        Distinguish operational fault reporting from report generation
        or report consumption.

        Examples:
        - "report a faulty charger" -> True
        - "report a station issue" -> True
        - "charger reports a critical fault" -> True
        - "generate station utilization reports" -> False
        """

        fault_reporting_patterns = [
            r"\breport\b\s+(?:a|an|the)\s+(?:faulty|broken|damaged)\b",
            r"\breport\b\s+(?:a|an|the)\s+(?:charger|station)\s+(?:fault|issue|problem)\b",
            r"\bcharger\b[^.\n]{0,60}\breports?\b[^.\n]{0,60}\b(?:fault|failure|critical fault|error)\b",
            r"\breport\b[^.\n]{0,60}\b(?:faulty charger|station issue|charger fault)\b",
        ]

        return any(
            re.search(pattern, text, re.IGNORECASE)
            for pattern in fault_reporting_patterns
        )

    @staticmethod
    def _has_explicit_reporting_requirement(
        matches: List[Dict[str, Any]],
    ) -> bool:
        """
        Reporting must be explicitly requested.

        Distinguish report-generation/consumption from operational
        fault reporting. For example:

        - "generate reports" -> reporting
        - "view financial reports" -> reporting
        - "report a faulty charger" -> not reporting
        - "charger reports a critical fault" -> not reporting
        """

        reporting_patterns = [
            r"\b(generate|create|produce|view|access|download|export|review)\b[^.\n]{0,80}\breports?\b",
            r"\breports?\b[^.\n]{0,80}\b(generate|create|produce|view|access|download|export|review)\b",
            r"\b(operational|financial|utilization|revenue|summary|performance)\s+reports?\b",
            r"\banalytics\b",
            r"\banaly[sz]\w*\b",
            r"\bstatistics\b",
            r"\bmetrics\b",
            r"\bperformance report\b",
            r"\bsummary report\b",
            r"\breporting and auditability\b",
        ]

        fault_reporting_patterns = [
            r"\breport\b\s+(?:a|an|the)\s+(?:faulty|broken|damaged)\b",
            r"\breport\b\s+(?:a|an|the)\s+(?:charger|station)\s+(?:fault|issue|problem)\b",
            r"\bcharger\b[^.\n]{0,60}\breports?\b[^.\n]{0,60}\b(?:fault|failure|critical fault|error)\b",
            r"\breport\b[^.\n]{0,60}\b(?:faulty charger|station issue|charger fault)\b",
        ]

        for req in matches:
            text = req["text"]

            if any(
                re.search(pattern, text, re.IGNORECASE)
                for pattern in fault_reporting_patterns
            ):
                continue

            if any(
                re.search(pattern, text, re.IGNORECASE)
                for pattern in reporting_patterns
            ):
                return True

        return False

    # ==================================================================
    # Capability modules
    # ==================================================================

    def _build_rule_module(
        self,
        rule: Dict[str, Any],
        matches: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        evidence = [
            str(match["id"])
            for match in matches
            if match.get("id")
        ]

        description = (
            f"Handles capabilities related to "
            f"{rule['name'].lower()}."
        )

        if evidence:
            description += (
                " Supported by requirement evidence: "
                + ", ".join(evidence[:8])
                + "."
            )

        return {
            "id": self._module_id(rule["key"]),
            "name": rule["name"],
            "description": description,
            "module_type": "service",
            "tech_stack": "Application API + relational data access",
            "responsibilities": list(rule["responsibilities"]),
            "api_endpoints": list(rule["endpoints"]),
            "pos_x": 150.0,
            "pos_y": 180.0,
            "is_ai_suggested": True,
            "status": "approved",
        }

    # ==================================================================
    # Conservative domain discovery
    # ==================================================================

    def _discover_domain_entities(
        self,
        requirements: List[Dict[str, Any]],
        used_capabilities: Set[str],
    ) -> List[Dict[str, Any]]:

        candidates: Dict[str, Dict[str, Any]] = {}

        for req in requirements:
            original = req["original"]

            raw_targets = [
                original.get("target_object"),
            ]

            action = str(
                original.get("action") or ""
            ).strip()

            target_from_action = self._target_after_action(action)

            if target_from_action:
                raw_targets.append(target_from_action)

            for raw_target in raw_targets:
                concept = self._clean_target(raw_target)

                if not concept:
                    continue

                canonical = self._canonical_entity(concept)

                if not canonical:
                    continue

                # Never create a generic entity module.
                if self._is_non_module_entity(canonical):
                    continue

                capability_key = self._entity_to_capability(canonical)

                if capability_key in used_capabilities:
                    continue

                if self._should_ignore_entity(canonical):
                    continue

                key = self._concept_key(canonical)

                entry = candidates.setdefault(
                    key,
                    {
                        "key": key,
                        "concept": canonical,
                        "requirements": [],
                    },
                )

                if req not in entry["requirements"]:
                    entry["requirements"].append(req)

        # Only retain genuinely repeated domain concepts.
        ranked = sorted(
            candidates.values(),
            key=lambda item: (
                len(item["requirements"]),
                -len(item["concept"]),
            ),
            reverse=True,
        )

        qualified = []

        for candidate in ranked:
            # One-off nouns are not enough evidence for a service.
            if len(candidate["requirements"]) < 2:
                continue

            qualified.append(candidate)

            # Keep architecture compact.
            if len(qualified) >= 4:
                break

        return qualified

    @staticmethod
    def _target_after_action(
        action: str,
    ) -> Optional[str]:

        if not action:
            return None

        match = re.match(
            r"^(?:search|manage|create|update|delete|view|"
            r"retrieve|record|store|display|track|maintain)"
            r"\s+(.+)$",
            action,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

        return None

    def _clean_target(
        self,
        target: Any,
    ) -> Optional[str]:

        if target is None:
            return None

        value = str(target).strip().lower()

        if not value:
            return None

        value = re.sub(
            r"^(the|a|an|their|his|her|our|your)\s+",
            "",
            value,
        )

        value = re.sub(
            r"\s+(are|is|was|were|for|from|with|by|in|on|at|"
            r"to|of|and|or|that|which|who)\s+.*$",
            "",
            value,
        )

        value = re.sub(
            r"[.,;:!?()\[\]{}]",
            "",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

        words = value.split()

        if len(words) > 4:
            return None

        meaningful = [
            word
            for word in words
            if word not in self.STOPWORDS
        ]

        if not meaningful:
            return None

        # Remove grammatical noise.
        if len(words) > 2:
            value = " ".join(meaningful)

        return value

    def _canonical_entity(
        self,
        concept: str,
    ) -> Optional[str]:

        if not concept:
            return None

        if concept in self.ENTITY_ALIASES:
            return self.ENTITY_ALIASES[concept]

        words = concept.split()
        normalized = []

        for word in words:
            if word.endswith("ies") and len(word) > 4:
                word = word[:-3] + "y"
            elif word.endswith("s") and len(word) > 3:
                word = word[:-1]

            normalized.append(word)

        concept = " ".join(normalized)

        if concept in self.ENTITY_ALIASES:
            return self.ENTITY_ALIASES[concept]

        return concept

    def _entity_to_capability(
        self,
        entity: str,
    ) -> Optional[str]:
        from backend.app.agents.taxonomy import ENTITY_TO_CAPABILITY
        return ENTITY_TO_CAPABILITY.get(entity)

    def _is_non_module_entity(
        self,
        entity: str,
    ) -> bool:

        normalized = entity.lower().strip()

        if normalized in self.NON_MODULE_ENTITIES:
            return True

        # Email is an infrastructure mechanism here unless the
        # requirements explicitly establish an email domain.
        if "email" in normalized:
            return True

        # Account is part of authentication/profile in this project.
        if "account" in normalized:
            return True

        # Generic UI concepts should not become domain services.
        if normalized in {
            "dashboard",
            "screen",
            "page",
            "interface",
            "user interface",
            "system behavior",
            "report",
            "reports",
        }:
            return True

        return False

    def _should_ignore_entity(
        self,
        entity: str,
    ) -> bool:

        words = set(entity.split())

        if not words:
            return True

        if words.issubset(self.STOPWORDS):
            return True

        if len(entity.split()) > 4:
            return True

        return False

    @staticmethod
    def _concept_key(
        concept: str,
    ) -> str:

        return re.sub(
            r"[^a-z0-9]+",
            "-",
            concept.lower(),
        ).strip("-")

    # ==================================================================
    # Generic domain module
    # ==================================================================

    def _build_domain_module(
        self,
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:

        concept = candidate["concept"]

        evidence = [
            str(req["id"])
            for req in candidate["requirements"]
            if req.get("id")
        ]

        slug = self._concept_key(concept)

        responsibilities = [
            f"Manage {concept}",
            f"Provide operations related to {concept}",
        ]

        description = (
            f"Provides application capabilities for "
            f"{concept} identified from multiple requirements."
        )

        if evidence:
            description += (
                " Supported by requirement evidence: "
                + ", ".join(evidence[:8])
                + "."
            )

        return {
            "id": self._module_id(
                f"domain-{slug}"
            ),
            "name": self._title_case(concept),
            "description": description,
            "module_type": "service",
            "tech_stack": "Application API + relational data access",
            "responsibilities": responsibilities,
            "api_endpoints": [
                f"/api/{slug}",
                f"/api/{slug}/{{id}}",
            ],
            "pos_x": 150.0,
            "pos_y": 180.0,
            "is_ai_suggested": True,
            "status": "approved",
        }

    # ==================================================================
    # Persistence
    # ==================================================================

    @staticmethod
    def _build_data_module() -> Dict[str, Any]:

        return {
            "id": "MOD-DATA",
            "name": "Application Data Store",
            "description": (
                "Provides persistent storage for entities and records "
                "required by the analyzed software requirements."
            ),
            "module_type": "database",
            "tech_stack": "Relational database",
            "responsibilities": [
                "Persist application entities",
                "Maintain data consistency",
                "Support application data retrieval",
            ],
            "api_endpoints": [],
            "pos_x": 400.0,
            "pos_y": 500.0,
            "is_ai_suggested": True,
            "status": "approved",
        }

    # ==================================================================
    # IDs / names
    # ==================================================================

    @staticmethod
    def _module_id(
        value: str,
    ) -> str:

        safe = re.sub(
            r"[^A-Za-z0-9]+",
            "-",
            value,
        ).strip("-").upper()

        return f"MOD-{safe}"

    @staticmethod
    def _title_case(
        value: str,
    ) -> str:

        return " ".join(
            word.capitalize()
            for word in value.split()
        )

    # ==================================================================
    # Layout
    # ==================================================================

    @staticmethod
    def _assign_positions(
        modules: List[Dict[str, Any]],
    ) -> None:

        gateway = next(
            (
                module
                for module in modules
                if module["module_type"] == "gateway"
            ),
            None,
        )

        database = next(
            (
                module
                for module in modules
                if module["module_type"] == "database"
            ),
            None,
        )

        services = [
            module
            for module in modules
            if module["module_type"] == "service"
        ]

        if gateway:
            gateway["pos_x"] = 400.0
            gateway["pos_y"] = 50.0

        for index, module in enumerate(services):
            column = index % 3
            row = index // 3

            module["pos_x"] = (
                150.0 + column * 250.0
            )

            module["pos_y"] = (
                180.0 + row * 170.0
            )

        if database:
            database["pos_x"] = 400.0
            database["pos_y"] = 500.0

    # ==================================================================
    # Conservative architecture relations
    # ==================================================================

    @staticmethod
    def _generate_relations(
        modules: List[Dict[str, Any]],
        gateway_id: Optional[str],
        requirements: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        module_ids = {
            module["id"]
            for module in modules
        }

        services = [
            module
            for module in modules
            if module["module_type"] == "service"
        ]

        relations = []
        seen = set()

        def add(
            source: str,
            target: str,
            relation_type: str,
            description: str,
        ) -> None:

            if source not in module_ids:
                return

            if target not in module_ids:
                return

            if source == target:
                return

            key = (
                source,
                target,
                relation_type,
            )

            if key in seen:
                return

            seen.add(key)

            relations.append(
                {
                    "source_module_id": source,
                    "target_module_id": target,
                    "relation_type": relation_type,
                    "description": description,
                }
            )

        # --------------------------------------------------------------
        # Gateway -> service
        #
        # This is a legitimate architectural boundary when a gateway
        # exists. It is the only place where the gateway fans out.
        # --------------------------------------------------------------

        if gateway_id:
            for service in services:
                add(
                    gateway_id,
                    service["id"],
                    "calls",
                    "Route application API requests to the service.",
                )

        # --------------------------------------------------------------
        # Service -> database
        #
        # Persistence is useful, but don't connect arbitrary services
        # that are only presentation-level to the database.
        # --------------------------------------------------------------

        persistence_services = {
            "MOD-AUTHENTICATION",
            "MOD-PROFILE",
            "MOD-NOTIFICATION",
            "MOD-SEARCH",
            "MOD-CART",
            "MOD-ORDER",
            "MOD-PAYMENT",
            "MOD-BOOKING",
            "MOD-ATTENDANCE",
            "MOD-FILE",
            "MOD-CHARGING-STATION",
            "MOD-CHARGING-SESSION",
            "MOD-MAINTENANCE",
        }

        for service in services:
            if service["id"] in persistence_services:
                add(
                    service["id"],
                    "MOD-DATA",
                    "reads_from",
                    "Persist and retrieve application data required by the service.",
                )

        # --------------------------------------------------------------
        # Explicit capability dependencies.
        #
        # Only add these when both modules actually exist.
        # --------------------------------------------------------------

        if (
            "MOD-AUTHENTICATION" in module_ids
            and "MOD-PROFILE" in module_ids
        ):
            add(
                "MOD-AUTHENTICATION",
                "MOD-PROFILE",
                "supports",
                "Authenticated identity is required to access protected profile operations.",
            )

        if (
            "MOD-AUTHENTICATION" in module_ids
            and "MOD-DASHBOARD" in module_ids
        ):
            add(
                "MOD-AUTHENTICATION",
                "MOD-DASHBOARD",
                "supports",
                "The dashboard is available after successful authentication.",
            )

        if (
            "MOD-AUTHENTICATION" in module_ids
            and "MOD-NOTIFICATION" in module_ids
        ):
            add(
                "MOD-AUTHENTICATION",
                "MOD-NOTIFICATION",
                "publishes_to",
                "Authentication-related events such as verification may trigger notifications.",
            )

        if (
            "MOD-PROFILE" in module_ids
            and "MOD-DASHBOARD" in module_ids
        ):
            add(
                "MOD-DASHBOARD",
                "MOD-PROFILE",
                "reads_from",
                "The dashboard may display account/profile information explicitly required by the requirements.",
            )

        # --------------------------------------------------------------
        # Domain-specific event dependencies retained from the original
        # architecture contract.
        # --------------------------------------------------------------

        notification_producers = {
            "MOD-ORDER",
            "MOD-PAYMENT",
            "MOD-BOOKING",
            "MOD-ATTENDANCE",
            "MOD-CHARGING-SESSION",
            "MOD-MAINTENANCE",
        }

        if "MOD-NOTIFICATION" in module_ids:
            for source_id in notification_producers:
                if source_id in module_ids:
                    add(
                        source_id,
                        "MOD-NOTIFICATION",
                        "publishes_to",
                        "The capability can emit an event that triggers a notification.",
                    )

        # --------------------------------------------------------------
        # Reporting dependencies.
        #
        # Reporting is only present when explicitly requested.
        # It may read application data, but it does not automatically
        # connect to every service.
        # --------------------------------------------------------------

        if "MOD-REPORTING" in module_ids:
            add(
                "MOD-REPORTING",
                "MOD-DATA",
                "reads_from",
                "Reporting reads persisted data required for explicitly requested reports or metrics.",
            )

        return relations