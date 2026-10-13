from typing import List, Dict, Any, Optional
import asyncio
import json
import logging
import re

from backend.app.agents.taxonomy import normalize_module_id, CANONICAL_MODULES

logger = logging.getLogger(__name__)


class TaskDecompositionAgent:
    """
    Requirement-driven Task Decomposition Agent.

    Pipeline:

        Requirement
             ↓
        Capability scoring
             ↓
        Epic
             ↓
        Feature
             ↓
        Task
             ↓
        Subtasks

    Classification gives highest importance to structured requirement
    fields (action / target_object / summary) and lower importance to
    free-form description text.

    This prevents incidental words such as "order" in a payment
    description from incorrectly classifying the requirement as an
    order-management task.
    """

    CAPABILITY_RULES = [
        {
            "key": "authentication",
            "epic_key": "authentication",
            "patterns": [
                r"\blog[\s-]*in\b",
                r"\blog[\s-]*out\b",
                r"\bsign[\s-]*in\b",
                r"\bsign[\s-]*up\b",
                r"\bauthenticat\w*\b",
                r"\bauthoriz\w*\b",
                r"\bpassword\w*\b",
                r"\bcredential\w*\b",
                r"\bpermission\w*\b",
                r"\brole[- ]based\b",
                r"\baccess control\b",
                r"\bregistration\b",
                r"\bregister\w*\b",
                r"\bcreate account\b",
                r"\baccount creation\b",
                r"\bauthentication session\b",
                r"\buser session\b",
                r"\bsession timeout\b",
                r"\bpassword recovery\b",
                r"\bforgot password\b",
                r"\breset password\b",
                r"\bmfa\b",
                r"\btwo-factor\b",
                r"\bkyc\b",
                r"\bverify customer signature\w*\b",
                r"\bphoto identity\b",
                r"\bsupervisor authorization\b",
                r"\bsupervisor override\b",
                r"\btokeniz\w*\b",
                r"\bpci-dss\b",
                r"\buser roles\b",
                r"\bsupervisor(?:y)?\s+override\b",
                r"\boverride\b",
                r"\bdatabase encryption\b",
            ],
            "epic_title": "Authentication & Access Management",
            "feature_title": "Authentication & Authorization",
            "module_id": "MOD-AUTHENTICATION",
            "base_hours": 10,
            "base_points": 3,
        },
        {
            "key": "search",
            "epic_key": "discovery",
            "patterns": [
                r"\bsearch\b",
                r"\bsearching\b",
                r"\bfilter\w*\b",
                r"\bquery\b",
                r"\bdiscover\w*\b",
                r"\bfind\b",
                r"\blook up\b",
            ],
            "epic_title": "Search & Discovery",
            "feature_title": "Search & Filtering",
            "module_id": "MOD-SEARCH",
            "base_hours": 8,
            "base_points": 3,
        },
        {
            "key": "booking",
            "epic_key": "scheduling",
            "patterns": [
                r"\bbook\w*\b",
                r"\breserv\w*\b",
                r"\bappointment\w*\b",
                r"\bschedul\w*\b",
                r"\bshopping cart\b",
                r"\bcart\b",
                r"\badd to cart\b",
                r"\bremove from cart\b",
                r"\bcheckout\b",
                r"\border\w*\b",
                r"\b(?!purchase\s+recommendation)purchase\w*\b",
                r"\bloan application\w*\b",
                r"\bapply for .* loan\b",
                r"\bapply\s+for\s+.*loans?\b",
                r"\bborrow\w*\b",
                r"\bholds?\b",
                r"\breplacement requests?\b",
                r"\binter-library\b",
                r"\bpurchase recommendations?\b",
            ],
            "epic_title": "Booking & Scheduling",
            "feature_title": "Booking & Scheduling",
            "module_id": "MOD-BOOKING",
            "base_hours": 12,
            "base_points": 3,
        },
        {
            "key": "payment",
            "epic_key": "commerce",
            "patterns": [
                r"\bpayment\w*\b",
                r"\bpay\b",
                r"\bpaid\b",
                r"\btransaction\w*\b",
                r"\brefund\w*\b",
                r"\bbilling\b",
                r"\binvoice\w*\b",
                r"\bfund transfer\w*\b",
                r"\bstanding instructions?\b",
                r"\bcash deposit\w*\b",
                r"\bcash withdrawal\w*\b",
                r"\bcashier check\w*\b",
                r"\blate fee\w*\b",
            ],
            "epic_title": "Commerce & Order Management",
            "feature_title": "Payment Processing",
            "module_id": "MOD-PAYMENT",
            "base_hours": 14,
            "base_points": 5,
        },
        {
            "key": "notification",
            "epic_key": "communication",
            "patterns": [
                r"\bnotif\w*\b",
                r"\balert\w*\b",
                r"\bremind\w*\b",
                r"\bemail\w*\b",
                r"\bsms\b",
                r"\bpush notification\b",
                r"\bsuspicious transaction\w*\b",
                r"\bcompromised credentials?\b",
            ],
            "epic_title": "Notifications & Communication",
            "feature_title": "Notifications",
            "module_id": "MOD-NOTIFICATION",
            "base_hours": 6,
            "base_points": 2,
        },
        {
            "key": "attendance",
            "epic_key": "attendance",
            "patterns": [
                r"\battendance\b",
                r"\battendances\b",
                r"\babsent\b",
                r"\babsence\b",
                r"\bpresent\b",
            ],
            "epic_title": "Attendance Management",
            "feature_title": "Attendance Tracking",
            "module_id": "MOD-ATTENDANCE",
            "base_hours": 10,
            "base_points": 3,
        },
        {
            "key": "reporting",
            "epic_key": "reporting",
            "patterns": [
                r"\breport\w*\b",
                r"\banalytics\b",
                r"\banaly[sz]\w*\b",
                r"\bstatistics\b",
                r"\bmetrics\b",
                r"\bdebt-to-income\b",
                r"\brepayment schedules?\b",
                r"\btax invoices?\b",
                r"\bitemized receipts?\b",
            ],
            "epic_title": "Reporting & Analytics",
            "feature_title": "Reporting & Analytics",
            "module_id": "MOD-REPORTING",
            "base_hours": 10,
            "base_points": 3,
        },
        {
            "key": "dashboard",
            "epic_key": "dashboard",
            "feature_key": "dashboard",
            "epic_title": "Dashboard",
            "feature_title": "Dashboard Functionality",
            "patterns": [
                r"\bdashboard\b",
                r"\bhome screen\b",
                r"\blanding page\b",
            ],
            "module_id": "MOD-DASHBOARD",
            "base_hours": 8,
            "base_points": 3,
        },
        {
            "key": "profile",
            "epic_key": "user-management",
            "patterns": [
                r"\bprofile\w*\b",
                r"\buser details\b",
                r"\buser information\b",
                r"\bpersonal information\b",
                r"\bdebit card\b",
                r"\bcredit card\b",
                r"\bcard activation\b",
                r"\btemporary freeze\b",
                r"\blimit adjustment\w*\b",
                r"\bwishlist\w*\b",
                r"\breviews? and rating\w*\b",
                r"\bproduct review\w*\b",
            ],
            "epic_title": "User & Profile Management",
            "feature_title": "Profile Management",
            "module_id": "MOD-PROFILE",
            "base_hours": 8,
            "base_points": 3,
        },
                {
            "key": "file",
            "epic_key": "documents",
            "patterns": [
                r"\bupload\w*\b",
                r"\bdownload\w*\b",
                r"\bfile\w*\b",
                r"\bdocument\w*\b",
                r"\battachment\w*\b",
                r"\buploaded\b",
                r"\bincome proofs?\b",
                r"\bproofs?\b",
                r"\bpacking slips?\b",
            ],
            "epic_title": "File & Document Management",
            "feature_title": "File Management",
            "module_id": "MOD-FILE",
            "base_hours": 8,
            "base_points": 3,
        },

        # --------------------------------------------------------------
        # EV / Charging-domain capabilities
        # These are vocabulary-driven and activate only when the
        # requirement contains matching charging-domain evidence.
        # --------------------------------------------------------------

        {
            "key": "charging_station",
            "epic_key": "charging-station",
            "patterns": [
                r"\bcharging station\w*\b",
                r"\bstation operator\w*\b",
                r"\bcharger identifier\w*\b",
                r"\bconnector type\w*\b",
                r"\bcharging speed\w*\b",
                r"\bstation-specific pricing\b",
                r"\bstation utilization\b",
                r"\bcharger availability\b",
                r"\bcharger operating hour\w*\b",
                r"\bcharging station registration\b",
                r"\bmanage charging station\w*\b",
                r"\bregister charging station\w*\b",
                r"\breal[- ]time charger[- ]status\b",
                r"\bcharger[- ]status\b",
                r"\bcharger status\b",
                r"\bmanually disabled\b",
                r"\bdisable\w*.*\bcharger\b",
            ],
            "epic_title": "Charging Station Management",
            "feature_title": "Charging Station Management",
            "module_id": "MOD-CHARGING-STATION",
            "base_hours": 12,
            "base_points": 3,
        },

        {
            "key": "charging_session",
            "epic_key": "charging-session",
            "patterns": [
                r"\bcharging session\w*\b",
                r"\bstart charging\b",
                r"\bcharging session status\b",
                r"\benergy consumed\b",
                r"\bcharging history\b",
                r"\bcharging-session state\b",
            ],
            "epic_title": "Charging Session Management",
            "feature_title": "Charging Session Management",
            "module_id": "MOD-CHARGING-SESSION",
            "base_hours": 12,
            "base_points": 3,
        },

        {
            "key": "maintenance",
            "epic_key": "maintenance",
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
            "epic_title": "Maintenance Management",
            "feature_title": "Maintenance Management",
            "module_id": "MOD-MAINTENANCE",
            "base_hours": 10,
            "base_points": 3,
        },
        {
            "key": "data",
            "epic_key": "data-management",
            "patterns": [
                r"\bdata store\b",
                r"\bdatabase\b",
                r"\bproduct catalog\b",
                r"\bcatalog management\b",
                r"\bmaster data\b",
                r"\binventory stock\b",
                r"\bstock reservation\b",
                r"\breserve stock\b",
                r"\baccount suspension\b",
                r"\bsuspend account\w*\b",
                r"\banonymiz\w*\b",
                r"\bretention\b",
                r"\bphysical condition\b",
                r"\bdamage\w*\b",
                r"\bfinancial ledger\b",
                r"\baccount balance\w*\b",
                r"\btransaction history\b",
                r"\bborrowed items?\b",
            ],
            "epic_title": "Data Management & Storage",
            "feature_title": "Data Persistence",
            "module_id": "MOD-DATA",
            "base_hours": 10,
            "base_points": 3,
        },
        {
            "key": "gateway",
            "epic_key": "gateway",
            "patterns": [
                r"\bgateway\b",
                r"\bapi gateway\b",
                r"\buptime\b",
                r"\bavailability\b",
                r"\blatency\b",
                r"\bthroughput\b",
                r"\breverse proxy\b",
            ],
            "epic_title": "API Gateway",
            "feature_title": "Gateway Operations",
            "module_id": "MOD-GATEWAY",
            "base_hours": 8,
            "base_points": 3,
        },
    ]

    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm

    async def _classify_requirements_semantic(
        self,
        requirements: List[Dict[str, Any]],
        modules: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Use the configured LLM adapter to classify requirements based on
        functional meaning, domain context, and candidate architectural modules.

        Returns a dictionary mapping requirement_id -> classification metadata:
        {
            "module_id": <resolved_module_id>,
            "confidence": float,
            "reasoning": str,
            "is_llm_classified": True,
            "classification_source": "llm",
        }
        """
        if not self.llm or not getattr(self.llm, "api_key", ""):
            return {}

        if not requirements or not modules:
            return {}

        candidate_lines = []
        for m in modules:
            mid = m.get("id", "")
            mname = m.get("name", "")
            mresp = "; ".join(m.get("responsibilities", []))
            mdesc = m.get("description", "")
            summary = mresp if mresp else mdesc
            candidate_lines.append(f"- ID: {mid} | Name: {mname} | Responsibilities: {summary}")
        candidate_modules_text = "\n".join(candidate_lines)

        results: Dict[str, Dict[str, Any]] = {}
        batch_size = 10

        for i in range(0, len(requirements), batch_size):
            batch = requirements[i : i + batch_size]
            batch_ids = {str(r.get("id", "")).strip() for r in batch if r.get("id")}
            seen_in_batch = set()

            req_lines = []
            for r in batch:
                rid = r.get("id", "")
                rsum = self._field_text(r.get("summary"))
                rdesc = self._field_text(r.get("description"))
                ractor = self._field_text(r.get("actor"))
                raction = self._field_text(r.get("action"))
                rtarget = self._field_text(r.get("target_object"))
                req_lines.append(
                    f"Requirement ID: {rid}\n"
                    f"  Summary: {rsum}\n"
                    f"  Description: {rdesc}\n"
                    f"  Actor: {ractor} | Action: {raction} | Target: {rtarget}"
                )
            requirements_text = "\n\n".join(req_lines)

            prompt = f"""You are ReqPilot AI, an expert enterprise software architect and requirements engineer.

Your task is to classify software requirements to the single MOST appropriate Architecture Module based on functional semantics, architectural responsibility, and domain context.

============================================================
AVAILABLE CANDIDATE ARCHITECTURE MODULES
============================================================
{candidate_modules_text}

============================================================
REQUIREMENTS TO CLASSIFY ({len(batch)} items)
============================================================
{requirements_text}

============================================================
CLASSIFICATION RULES
============================================================
1. Assign every requirement to the single best-fitting candidate module ID from the candidate modules list above.
2. Rely on primary functional semantics and business capability rather than superficial keywords:
   - Primary Capability Precedence: Classify by the primary business capability being delivered:
     * User authentication, login credentials, passwords, MFA, customer registration with KYC verification and MFA login, sessions, roles, permissions, RBAC, tellers verifying customer signatures or photo identity documents, circulation desk staff verifying patron membership status and active hold privileges, supervisory approval of high-value transactions, access restriction policies (security rules about who can access system resources, e.g., "maintenance staff should only access maintenance requests assigned to them or their team" is an access-control security rule → AUTHENTICATION; contrast with "maintenance staff should be able to view assigned charger faults" which is an operational function → MAINTENANCE), supervisory override approvals, scanning/verifying patron card barcodes or identity, cryptographic data protection (encryption at rest / in transit like AES-256 / TLS 1.3), and regulatory compliance (e.g., PCI-DSS) belong to Authentication & Authorization (MOD-AUTHENTICATION). DISAMBIGUATION: account suspension/termination (e.g., "suspend accounts that violate system policies") belongs to MOD-DATA, not MOD-AUTHENTICATION.
       * Checking out items, initiating loans, renewals, loan applications, reservations, viewing active reservations (e.g., station operators viewing active reservations and charging sessions belongs to Booking & Scheduling MOD-BOOKING), slot booking holds, scheduling appointments, order placement, shopping cart checkout, replacement requests (note: inventory stock reservation, returned item processing, and warehouse package dispatching belong to Application Data Store MOD-DATA, not Booking), inter-library loan requests, purchase recommendations, configuring loan durations, maximum borrowing limits, renewal rules, and fine rate schedules, prohibiting/rejecting new reservations on disabled or active chargers (e.g., preventing a charger marked unavailable for maintenance from accepting reservations, a disabled charger must not accept new reservations, a charger becoming unavailable for new reservations when a fault is detected, or a charger becoming unavailable for new reservations when a session starts), and underwriting officers approving or rejecting loans belong to Booking & Scheduling (MOD-BOOKING). DISAMBIGUATION: automatically reserving stock items when checkout begins belongs to MOD-DATA, not MOD-BOOKING; circulation staff processing returned items, inspecting condition, and returning to inventory belongs to MOD-DATA, not MOD-BOOKING; loan officers reviewing loan applications and uploaded income proofs belongs to MOD-FILE; calculating debt-to-income ratios belongs to MOD-REPORTING; tracking loan installments and calculating interest formulas belongs to MOD-DATA. Configuring "reservation policies" as part of a system-wide notification and reservation policy setting belongs to MOD-NOTIFICATION, not MOD-BOOKING.
     * Processing payments, viewing hospital bills and payment receipts, making eligible payments through the portal or online gateway, scheduling recurring and future-dated payments, credit card transactions, paying fines and late fees, fee calculation, fund transfers, billing, invoices, generating an invoice for each completed paid charging session (note: drivers viewing their past charging history and invoices belongs to Charging Session Management MOD-CHARGING-SESSION), deposits, withdrawals, refunds, releasing reserved stock upon payment timeout or failure belong to Payment Management (MOD-PAYMENT).
     * Dispatched alerts, customer reporting of suspicious transactions or compromised credentials, push messages, SMS, automated email notifications, suspicious transaction warning alerts, and configuring policies narrowly focused on notification delivery or messaging alerts belong to Notification Service (MOD-NOTIFICATION) (e.g., alerting staff when a fault occurs is primarily a notification; administrators configuring notification and reservation communication alerts belongs here). DISAMBIGUATION: cross-cutting administrative configuration that combines multiple unrelated system policies (such as scheduling, billing, notification, and retention together) belongs to system data administration (MOD-DATA), not MOD-NOTIFICATION.
     * Master entity records, persistent business records, record-change history (maintaining records of changes made to domain entities, audit trails recording administrative actions, password resets, or financial adjustments, preserving records and logs for retention schedules/audit purposes, e.g. 7-10 years), cross-cutting administrative configuration combining multiple unrelated system policies, product catalog management (descriptions, images, variants, pricing), warehouse inventory stock levels, viewing real-time product details, specifications, customer reviews, and stock availability (note: directly retrieving and viewing record details or stock levels belongs to MOD-DATA, whereas executing search queries to locate records in a collection belongs to MOD-SEARCH), automatically reserving stock items when checkout begins, updating carrier tracking numbers, dispatching packages and recording package dispatches in inventory stock records, balance states, viewing complete account balances and real-time transaction history for savings and checking accounts, viewing complete order history and real-time shipment tracking status, viewing borrowed items, due dates, renewal counts, reading history, patrons viewing real-time catalog availability, shelf location, and call numbers, processing returned items, inspecting material condition, and returning items to inventory, financial ledger formulas (calculating interest formulas, tracking monthly installment payments and flagging delinquent loans, immutable recording of all transactions in a tamper-resistant financial ledger, automatically monitoring transactions against AML rule thresholds), account suspension (e.g., suspending accounts that violate policies — IMPORTANT: account suspension is DATA, not AUTHENTICATION), driver account retention schedules, and data anonymization lifecycle belong to Application Data Store (MOD-DATA). DISAMBIGUATION: monitoring transactions against AML rule thresholds belongs to MOD-DATA (financial ledger threshold rules), not MOD-REPORTING.
     * User profile details, contact information, addresses, wishlist management, customer reviews and ratings, debit card activation, temporary card freeze/unfreeze, PIN management, and card spending limit adjustments belong to Profile Management (MOD-PROFILE) (note: registration/KYC/MFA belongs to Authentication & Authorization MOD-AUTHENTICATION; viewing account balances, complete order history, reading history, and borrowed items belongs to Application Data Store MOD-DATA, not Profile).
     * Packing slips, document uploads, file attachments, downloadable statements, loan officers reviewing customer loan applications, credit scores, and uploaded income proofs for underwriting belong to File & Document Management (MOD-FILE).
     * Generating cross-system or domain analytical reports (e.g., generating reports for stations, reports identifying station/charger/period status totals, generating regulatory compliance reports), aggregated business metrics, calculating debt-to-income ratios and preliminary repayment schedules, business statistics, revenue summaries, recording cross-cutting operational audit logs across system transitions (when documented under reporting architecture responsibilities), and tax invoice generation belong to Reporting & Analytics (MOD-REPORTING). (Note: station operators viewing live station utilization/revenue belongs to Charging Station Management MOD-CHARGING-STATION, whereas generating or producing reports belongs to MOD-REPORTING).
     * Executing search queries, keyword searching, faceted filters, resource lookup, locating matching records in a collection (e.g., customer support agents searching or looking up customer orders by ID, email, date, or status, staff searching for existing entity records, and support agents looking up customer accounts, orders, and delivery timelines) belong to Search & Discovery (MOD-SEARCH). Classify by the requested operation (querying/searching a collection belongs to MOD-SEARCH vs. directly storing, updating, or retrieving specific record contents which belongs to MOD-DATA). Note: Searching or locating physical charging stations by location, speed, or availability belongs to Charging Station Management (MOD-CHARGING-STATION). Directly viewing real-time details, stock availability, shelf location, and call numbers belongs to Application Data Store (MOD-DATA).
     * Cross-cutting network SLA, system availability, uptime (e.g., 99.9% platform availability), API latency, throughput, and gateway reverse proxy routing belong to API Gateway (MOD-GATEWAY).
   - Domain-Specific Modules (take precedence over generic capabilities when present):
     * Charging Station Management (MOD-CHARGING-STATION): Managing physical charging stations/chargers, operational charger state (temporarily enabling or disabling a charger for maintenance), connector specifications, setting station-specific pricing rules, drivers searching charging stations by location/speed/availability or viewing availability under concurrent load (performance and responsiveness when thousands of drivers search stations or view availability simultaneously), station operators viewing station utilization and revenue, and station operators only modifying stations assigned to their organization (scoping station management by organization belongs to MOD-CHARGING-STATION, not MOD-AUTHENTICATION). (Note: generating reports belongs to MOD-REPORTING).
     * Charging Session Management (MOD-CHARGING-SESSION): Starting/stopping charging sessions, live charging telemetry, power metering, energy consumed (kWh), session duration, and drivers viewing charging history and session invoices.
     * Maintenance Management (MOD-MAINTENANCE): Reporting equipment faults/malfunctions, assigning technician work orders, updating maintenance request status, maintenance staff viewing assigned charger faults and maintenance requests (operational task), administrator management of the full workforce and asset system — managing drivers, operators, maintenance staff, stations, chargers, pricing rules, and system settings (IMPORTANT: when an administrator manages all system users and assets including maintenance staff, this is MAINTENANCE, not CHARGING-STATION), and recording repair inspections. DISAMBIGUATION: access restriction requirements (who can access which data, e.g., "maintenance staff should only access requests assigned to them") belong to MOD-AUTHENTICATION, not MOD-MAINTENANCE.
     * Department Management (MOD-DOMAIN-DEPARTMENT): Organizational clinical/administrative department boundaries.
3. You MUST ONLY select a module ID that is present in the Candidate Architecture Modules list. Do NOT invent new module IDs.
4. If a requirement is cross-cutting or ambiguous, select the module that implements the primary business capability.
5. Provide a confidence score between 0.0 and 1.0 and a brief one-sentence engineering reasoning.
"""

            schema = """{
  "classifications": [
    {
      "requirement_id": "FR-001",
      "module_id": "MOD-AUTHENTICATION",
      "confidence": 0.95,
      "reasoning": "Handles user login and credential verification."
    }
  ]
}
"""

            try:
                response = await self.llm.generate_json(prompt, schema)
                if not response or not isinstance(response, dict):
                    logger.warning("LLM returned non-dict or None for requirement classification batch %d. Falling back to deterministic engine for this batch.", i // batch_size + 1)
                    continue

                classifications = response.get("classifications", [])
                if not isinstance(classifications, list):
                    logger.warning("LLM response missing 'classifications' list in batch %d. Falling back to deterministic engine.", i // batch_size + 1)
                    continue

                for item in classifications:
                    if not isinstance(item, dict):
                        continue
                    req_id = str(item.get("requirement_id", "")).strip()
                    proposed_mod_id = str(item.get("module_id", "")).strip()
                    raw_conf = item.get("confidence")
                    try:
                        confidence = float(raw_conf) if raw_conf is not None else 0.85
                    except (ValueError, TypeError):
                        confidence = 0.85
                    # Constrain confidence strictly to [0.0, 1.0]
                    confidence = max(0.0, min(1.0, confidence))

                    reasoning = str(item.get("reasoning", "")).strip()

                    if not req_id or not proposed_mod_id:
                        continue

                    # Validation 1: Requirement ID must belong to current batch
                    if req_id not in batch_ids:
                        logger.warning(
                            "LLM proposed classification for requirement '%s' which is not in current batch %s. Rejecting.",
                            req_id,
                            list(batch_ids),
                        )
                        continue

                    # Validation 2: Reject duplicates within batch
                    if req_id in seen_in_batch:
                        logger.warning(
                            "Duplicate classification returned for requirement '%s' in batch %d. Ignoring duplicate.",
                            req_id,
                            i // batch_size + 1,
                        )
                        continue
                    seen_in_batch.add(req_id)

                    # Validation 3: Validate proposed_mod_id against candidate modules.
                    # Direct match against candidate modules takes strict precedence to preserve dynamic domain modules.
                    resolved_id = self._resolve_architecture_module_id(proposed_mod_id, modules)
                    if not resolved_id:
                        norm_id = normalize_module_id(proposed_mod_id)
                        if norm_id and norm_id != proposed_mod_id:
                            resolved_id = self._resolve_architecture_module_id(norm_id, modules)

                    if resolved_id:
                        results[req_id] = {
                            "module_id": resolved_id,
                            "confidence": confidence,
                            "reasoning": reasoning,
                            "is_llm_classified": True,
                            "classification_source": "llm",
                        }
                    else:
                        logger.warning(
                            "LLM proposed invalid/unresolvable module '%s' for requirement '%s'. "
                            "Rejecting and falling back to deterministic classifier.",
                            proposed_mod_id,
                            req_id,
                        )

            except Exception as e:
                logger.warning(
                    "Error during LLM classification batch %d: %s. Continuing with fallback.",
                    i // batch_size + 1,
                    e,
                )

            # Defensive throttling between batches to respect rate limits
            if i + batch_size < len(requirements):
                await asyncio.sleep(0.5)

        return results

    def _classification_for_resolved_module(
        self,
        req: Dict[str, Any],
        resolved_module_id: str,
        modules: List[Dict[str, Any]],
        llm_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Construct a structured classification dictionary for a requirement whose
        architecture module was semantically resolved by LLM.
        """
        matched_mod = None
        for m in modules:
            mid = str(m.get("id") or "").strip()
            if mid == resolved_module_id:
                matched_mod = m
                break

        mod_name = matched_mod.get("name", "Application Service") if matched_mod else "Application Service"
        mod_desc = matched_mod.get("description", "") if matched_mod else ""

        rule_match = None
        for rule in self.CAPABILITY_RULES:
            rid = str(rule.get("module_id") or "").strip()
            if (
                rid == resolved_module_id
                or resolved_module_id.upper().endswith(f"-{rid.upper()}")
                or rule.get("name", "").lower() == mod_name.lower()
            ):
                rule_match = rule
                break

        if rule_match:
            epic_key = rule_match["epic_key"]
            feature_key = rule_match.get("feature_key", rule_match["key"])
            epic_title = rule_match["epic_title"]
            epic_description = (
                f"Implementation of capabilities related to {rule_match['epic_title'].lower()}."
            )
            feature_title = rule_match["feature_title"]
            feature_description = (
                f"Implement {rule_match['feature_title'].lower()}."
            )
            base_hours = rule_match.get("base_hours", 10)
            base_points = rule_match.get("base_points", 3)
        else:
            slug = re.sub(r"[^a-z0-9]+", "-", mod_name.lower()).strip("-")
            epic_key = slug or "domain-module"
            feature_key = f"{slug}-operations"
            epic_title = mod_name
            epic_description = mod_desc or f"Implementation of functionality related to {mod_name}."
            feature_title = f"{self._title_case(mod_name)} Operations"
            feature_description = f"Implement operations and services for {mod_name}."
            base_hours = 12
            base_points = 3

        return {
            "key": epic_key,
            "epic_key": epic_key,
            "feature_key": feature_key,
            "epic_title": epic_title,
            "epic_description": epic_description,
            "feature_title": feature_title,
            "feature_description": feature_description,
            "module_id": resolved_module_id,
            "base_hours": base_hours,
            "base_points": base_points,
            "known_capability": rule_match is not None,
            "is_llm_classified": bool(llm_meta and llm_meta.get("is_llm_classified")),
            "classification_source": llm_meta.get("classification_source", "llm") if llm_meta else "deterministic_fallback",
            "confidence": float(llm_meta.get("confidence", 0.9)) if llm_meta else 0.5,
            "reasoning": str(llm_meta.get("reasoning", "")) if llm_meta else "Deterministic fallback",
        }

    def decompose_requirements_sync(
        self,
        requirements,
        modules=None,
    ) -> Dict[str, Any]:
        """Synchronous deterministic fallback decomposition."""
        return self._decompose_internal(requirements, modules=modules, llm_classifications=None)

    async def decompose_requirements(
        self,
        requirements,
        modules=None,
    ) -> Dict[str, Any]:
        """
        Decompose requirements into Epics, Features, and Tasks with semantic
        architecture assignment.

        If LLM is configured and operational, classifies requirements based on
        semantic meaning and context against candidate architecture modules.
        If LLM is offline, unconfigured, or encounters errors, safely falls back
        to deterministic rule classification.
        """
        llm_classifications = None
        if self.llm and getattr(self.llm, "api_key", "") and modules:
            try:
                llm_classifications = await self._classify_requirements_semantic(
                    requirements,
                    modules,
                )
            except Exception as e:
                logger.warning(
                    "Error during LLM semantic classification: %s. Falling back to deterministic engine.",
                    e,
                )
                llm_classifications = None

        return self._decompose_internal(
            requirements,
            modules=modules,
            llm_classifications=llm_classifications,
        )

    def _decompose_internal(
        self,
        requirements,
        modules=None,
        llm_classifications=None,
    ) -> Dict[str, Any]:

        epics = []
        features = []
        tasks = []
        dependencies = []

        epic_map = {}
        feature_map = {}

        task_counter = 1

        for req in requirements:

            req_id = req.get("id")

            if not req_id:
                continue

            if llm_classifications and req_id in llm_classifications:
                llm_meta = llm_classifications[req_id]
                resolved_module_id = llm_meta.get("module_id")
                classification = self._classification_for_resolved_module(
                    req,
                    resolved_module_id,
                    modules or [],
                    llm_meta,
                )
            else:
                classification = self._classify_requirement(req)

                logical_module_id = classification.get("module_id")

                # ------------------------------------------------------
                # First try the classifier's module against the actual
                # architecture.
                # ------------------------------------------------------
                resolved_module_id = self._resolve_architecture_module_id(
                    logical_module_id,
                    modules or [],
                )

                # ------------------------------------------------------
                # Semantic fallback when the classifier's logical module
                # is not represented by the current architecture.
                #
                # This covers both:
                #   - synthetic MOD-DOMAIN-* classifications
                #   - known generic capabilities such as MOD-SEARCH
                #     that are absent from the current architecture
                # ------------------------------------------------------
                if resolved_module_id is None:
                    semantic_text = " ".join(
                        [
                            self._field_text(req.get("summary")),
                            self._field_text(req.get("description")),
                            self._field_text(req.get("target_object")),
                            self._field_text(req.get("action")),
                        ]
                    ).lower()

                    fallback_module_id = None

                    # Account authorization / suspension / KYC / Identity
                    if re.search(
                        r"\b(?:suspend|suspension|authorization|authoriz|"
                        r"access control|access restriction|permission|"
                        r"authenticat\w*|login|log-in|sign-in|mfa|two-factor|"
                        r"kyc|signature|identity verification)\w*\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-AUTHENTICATION"

                    # Payments, wire/fund transfers, deposits, withdrawals, fees
                    elif re.search(
                        r"\b(?:payment\w*|pay\b|paid|fund transfer\w*|wire transfer\w*|"
                        r"electronic transfer\w*|money transfer\w*|transfer funds|account transfer\w*|"
                        r"deposit\w*|cash deposit\w*|withdrawal\w*|"
                        r"cash withdrawal\w*|cashier check\w*|late fee\w*|fines?|"
                        r"billing|invoice\w*|refund\w*)\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-PAYMENT"

                    # Bookings, reservations, loans, checkouts, holds, circulation renewals
                    elif re.search(
                        r"\b(?:book\w*|reserv\w*|appointment\w*|schedul\w*|"
                        r"checkout|shopping cart|cart\b|place a hold|renew\w*|"
                        r"loan application\w*|apply for .* loan|apply\s+for\s+.*loans?|inter-library|"
                        r"purchase recommendation|borrow\w*|check out physical)\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-BOOKING"

                    # User profile, card settings, wishlists, reviews
                    elif re.search(
                        r"\b(?:profile\w*|wishlist\w*|debit card\w*|credit card\w*|"
                        r"card activation|temporary freeze|limit adjustment\w*|"
                        r"product review\w*|reviews? and rating\w*)\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-PROFILE"

                    # Documents, file attachments, statement downloads, EOD reconciliation
                    elif re.search(
                        r"\b(?:upload\w*|download\w*|attachment\w*|document\w*|"
                        r"monthly statement\w*|tax certificate\w*|cash drawer reconciliation|"
                        r"export\w*|eod\b)\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-FILE"

                    # Notifications, alerts, messages, SMS, push
                    elif re.search(
                        r"\b(?:notif\w*|alert\w*|sms\b|push notification\w*|"
                        r"email notification\w*|remind\w*|suspicious transaction\w*)\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-NOTIFICATION"

                    # Reporting, analytics, metrics, debt ratios
                    elif re.search(
                        r"\b(?:report\w*|analytics|statistic\w*|metrics?|"
                        r"debt-to-income|underwriting|summary report\w*)\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-REPORTING"

                    # Search and catalog discovery
                    elif re.search(
                        r"\b(?:search\w*|filter\w*|opac\b|catalog search\w*|"
                        r"find\b|discover\w*|query\w*)\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-SEARCH"

                    # Persistent records, audit logs, anonymization, retention, core data, catalog management
                    elif re.search(
                        r"\b(?:audit|audit log|records?|anonymiz\w*|"
                        r"retention|retain\w*|data storage|data store|"
                        r"product catalog|catalog management|manage.*catalog|variants?|"
                        r"suspend account\w*|account suspension|"
                        r"catalog availability|shelf location|product details?|"
                        r"inventory|borrowed items?|transaction history|account balance)\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-DATA"

                    # Cross-cutting system quality characteristics
                    elif re.search(
                        r"\b(?:performance|responsive|responsiveness|"
                        r"availability|reliability|scalability|"
                        r"uptime|response time)\b",
                        semantic_text,
                        re.IGNORECASE,
                    ):
                        fallback_module_id = "MOD-GATEWAY"

                    if not fallback_module_id:
                        fallback_module_id = "MOD-DATA"

                    resolved_module_id = self._resolve_architecture_module_id(
                        fallback_module_id,
                        modules or [],
                    )

                classification = {
                    **classification,
                    "module_id": resolved_module_id,
                    "is_llm_classified": False,
                    "classification_source": "deterministic_fallback",
                    "confidence": 0.5,
                    "reasoning": "Deterministic rule-based classification fallback",
                }

            epic_key = classification["epic_key"]
            feature_key = classification["feature_key"]

            # ------------------------------------------------------
            # Epic
            # ------------------------------------------------------

            if epic_key not in epic_map:

                epic_id = f"EPIC-{len(epic_map) + 1:02d}"

                epic = {
                    "id": epic_id,
                    "title": classification["epic_title"],
                    "description": classification[
                        "epic_description"
                    ],
                }

                epic_map[epic_key] = epic
                epics.append(epic)

            epic = epic_map[epic_key]

            # ------------------------------------------------------
            # Feature
            # ------------------------------------------------------

            feature_identity = (
                f"{epic_key}:{feature_key}"
            )

            if feature_identity not in feature_map:

                feature_id = (
                    f"FEAT-{len(feature_map) + 1:02d}"
                )

                feature = {
                    "id": feature_id,
                    "epic_id": epic["id"],
                    "title": classification[
                        "feature_title"
                    ],
                    "description": classification[
                        "feature_description"
                    ],
                }

                feature_map[
                    feature_identity
                ] = feature

                features.append(feature)

            feature = feature_map[
                feature_identity
            ]

            # ------------------------------------------------------
            # Task
            # ------------------------------------------------------

            task_id = (
                f"TASK-{task_counter:03d}"
            )

            task_counter += 1

            complexity = self._estimate_complexity(
                req,
                classification,
            )

            hours, points = self._estimate_effort(
                classification,
                complexity,
            )

            priority = self._normalize_priority(
                req.get("priority")
            )

            acceptance = req.get(
                "acceptance_criteria"
            )

            if not acceptance:
                acceptance = [
                    f"Requirement {req_id} is implemented.",
                    "The documented acceptance conditions are satisfied.",
                    "Relevant automated tests pass.",
                ]

            task = {
                "id": task_id,
                "epic_id": epic["id"],
                "feature_id": feature["id"],
                "requirement_id": req_id,
                "module_id": classification[
                    "module_id"
                ],
                "required_skills": self._derive_required_skills(
                    classification,
                    modules or [],
                ),
                "title": self._task_title(
                    req,
                    classification,
                ),
                "description": self._task_description(
                    req,
                    classification,
                ),
                "complexity": complexity,
                "estimated_hours": hours,
                "story_points": points,
                "priority": priority,
                "status": "todo",
                "assignee_name": "Unassigned",
                "sprint_name": self._sprint_for_task(
                    task_counter
                ),
                "subtasks": self._generate_subtasks(
                    req
                ),
                "acceptance_criteria": acceptance,
                "depends_on": [],
                "is_ai_suggested": classification.get("is_llm_classified", False),
                "classification_source": classification.get("classification_source", "deterministic_fallback"),
                "confidence": classification.get("confidence", 0.5),
                "classification_reasoning": classification.get("reasoning", ""),
            }

            tasks.append(task)

        self._generate_dependencies(
            tasks,
            dependencies,
        )

        return {
            "epics": epics,
            "features": features,
            "tasks": tasks,
            "dependencies": dependencies,
            "classification_metadata": {
                "llm_used": bool(self.llm and getattr(self.llm, "api_key", "") and llm_classifications is not None),
                "llm_classified_count": sum(1 for t in tasks if t.get("is_ai_suggested")),
                "fallback_classified_count": sum(1 for t in tasks if not t.get("is_ai_suggested")),
                "total_requirements": len(tasks),
            },
        }

        # ================================================================
    # Classification
    # ================================================================

    def _classify_requirement(
        self,
        req: Dict[str, Any],
    ) -> Dict[str, Any]:

        summary = self._field_text(
            req.get("summary")
        )

        action = self._field_text(
            req.get("action")
        )

        target = self._field_text(
            req.get("target_object")
        )

        description = self._field_text(
            req.get("description")
        )

        req_type = self._field_text(
            req.get("req_type")
        ).lower().strip()

        normalized_summary = summary.lower()
        normalized_description = description.lower()

        cross_domain_text = (
            normalized_summary
            + " "
            + normalized_description
        )

        # --------------------------------------------------------------
        # Cross-cutting semantic preclassification.
        #
        # These rules execute before capability scoring because some
        # system-level requirements do not match a domain capability
        # strongly enough to enter the normal semantic-disambiguation
        # branch.
        # --------------------------------------------------------------

        # Data/audit/retention/anonymization/account-governance concerns.
        cross_cutting_data_requirement = (
            (
                re.search(
                    r"\b(?:audit log|audit logs|audit purposes?|"
                    r"retention|retained|anonymiz(?:e|ed|ation))\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:record(?:s|ed)?|available|retained|"
                    r"retention|anonymiz(?:e|ed|ation)|restore|"
                    r"restored|administrative actions?)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
            )
            or (
                re.search(
                    r"\b(?:maintenance records?|audit logs?)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:audit|retention|retained|available)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
            )
            or (
                re.search(
                    r"\b(?:account|accounts)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:anonymiz(?:e|ed|ation)|retention|"
                    r"retained|suspend|suspension)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
            )
            or (
                re.search(
                    r"\b(?:view\w*|display\w*|retrieve\w*)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:account balance|transaction history|order history|borrowed items|active borrowed|loan status)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
            )
            or (
                re.search(
                    r"\b(?:immutably recorded|tamper-resistant|audit trail|retain.*records|store.*records)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
            )
        )

        if cross_cutting_data_requirement:
            return {
                "key": "data-management",
                "epic_key": "data-management",
                "feature_key": "data-management",
                "epic_title": "Data Management",
                "epic_description": (
                    "Implementation of requirements related to "
                    "application data management."
                ),
                "feature_title": "Data Management",
                "feature_description": (
                    "Deliver functionality required for "
                    "application data management."
                ),
                "module_id": "MOD-DATA",
                "base_hours": 8,
                "base_points": 3,
                "known_capability": True,
            }

        # Supervisory override / threshold authorization (access control concern)
        if re.search(r"\b(?:supervisory override|supervisor override|supervisor authorization)\b", cross_domain_text, re.IGNORECASE):
            auth_rule = next((rule for rule in self.CAPABILITY_RULES if rule["key"] == "authentication"), None)
            if auth_rule:
                return {
                    "key": auth_rule["key"],
                    "epic_key": auth_rule["epic_key"],
                    "feature_key": auth_rule["key"],
                    "epic_title": auth_rule["epic_title"],
                    "epic_description": "Implementation of requirements related to authentication & authorization.",
                    "feature_title": auth_rule["feature_title"],
                    "feature_description": "Deliver functionality required for authorization and supervisory override.",
                    "module_id": auth_rule["module_id"],
                    "base_hours": auth_rule["base_hours"],
                    "base_points": auth_rule["base_points"],
                    "known_capability": True,
                }

        # Library patron membership verification
        if re.search(r"\bverify\s+patron\s+membership\b", cross_domain_text, re.IGNORECASE):
            auth_rule = next((rule for rule in self.CAPABILITY_RULES if rule["key"] == "authentication"), None)
            if auth_rule:
                return {
                    "key": auth_rule["key"],
                    "epic_key": auth_rule["epic_key"],
                    "feature_key": auth_rule["key"],
                    "epic_title": auth_rule["epic_title"],
                    "epic_description": "Implementation of requirements related to patron identity and membership verification.",
                    "feature_title": auth_rule["feature_title"],
                    "feature_description": "Deliver functionality required for patron membership verification.",
                    "module_id": auth_rule["module_id"],
                    "base_hours": auth_rule["base_hours"],
                    "base_points": auth_rule["base_points"],
                    "known_capability": True,
                }

        # Domain-specific EV station capability requirements.
        #
        # These are intentionally checked before generic system-level
        # performance/availability classification. Terms such as
        # "station search", "charger availability", and "waiting time"
        # describe charging-station capabilities, not the availability
        # of the overall application.
        ev_station_domain_requirement = (
            re.search(
                r"\b(?:charging station|charging stations|"
                r"charger|chargers|charging point|charging points)\b",
                cross_domain_text,
                re.IGNORECASE,
            )
            and re.search(
                r"\b(?:search|availability|available|"
                r"waiting time|wait time|estimated waiting)\b",
                cross_domain_text,
                re.IGNORECASE,
            )
        )

        if ev_station_domain_requirement:
            station_rule = next(
                (
                    rule
                    for rule in self.CAPABILITY_RULES
                    if rule["key"] == "charging_station"
                ),
                None,
            )

            if station_rule:
                return {
                    "key": station_rule["key"],
                    "epic_key": station_rule["epic_key"],
                    "feature_key": station_rule["key"],
                    "epic_title": station_rule["epic_title"],
                    "epic_description": (
                        f"Implementation of requirements related to "
                        f"{station_rule['epic_title'].lower()}."
                    ),
                    "feature_title": station_rule["feature_title"],
                    "feature_description": (
                        f"Deliver functionality required for "
                        f"{station_rule['feature_title'].lower()}."
                    ),
                    "module_id": station_rule["module_id"],
                    "base_hours": station_rule["base_hours"],
                    "base_points": station_rule["base_points"],
                    "known_capability": True,
                }

        # Station search can sometimes be normalized by the extractor as
        # generic "system behavior". Preserve the domain meaning from the
        # requirement text rather than routing it to the generic gateway.
        ev_station_search_requirement = (
            re.search(
                r"\b(?:station search|search charging stations|"
                r"search stations)\b",
                cross_domain_text,
                re.IGNORECASE,
            )
        )

        if ev_station_search_requirement:
            station_rule = next(
                (
                    rule
                    for rule in self.CAPABILITY_RULES
                    if rule["key"] == "charging_station"
                ),
                None,
            )

            if station_rule:
                return {
                    "key": station_rule["key"],
                    "epic_key": station_rule["epic_key"],
                    "feature_key": station_rule["key"],
                    "epic_title": station_rule["epic_title"],
                    "epic_description": (
                        f"Implementation of requirements related to "
                        f"{station_rule['epic_title'].lower()}."
                    ),
                    "feature_title": station_rule["feature_title"],
                    "feature_description": (
                        f"Deliver functionality required for "
                        f"{station_rule['feature_title'].lower()}."
                    ),
                    "module_id": station_rule["module_id"],
                    "base_hours": station_rule["base_hours"],
                    "base_points": station_rule["base_points"],
                    "known_capability": True,
                }

        # System-level performance requirements.
        system_performance_requirement = (
            req_type == "non_functional"
            and re.search(
                r"\b(?:performance|responsive|response time|"
                r"latency|throughput|concurrent|simultaneously)\b",
                cross_domain_text,
                re.IGNORECASE,
            )
        )

        # System-level availability/reliability requirements.
        system_availability_requirement = (
            req_type == "non_functional"
            and re.search(
                r"\b(?:(?:system|service|application|overall)\s+(?:availability|reliability)|"
                r"bed availability|doctor availability|consultation time slot\w*|"
                r"24/7|uptime|planned maintenance)\b",
                cross_domain_text,
                re.IGNORECASE,
            )
        )

        if (
            system_performance_requirement
            or system_availability_requirement
        ):
            return {
                "key": "system-gateway",
                "epic_key": "system-gateway",
                "feature_key": "system-gateway",
                "epic_title": "System Gateway",
                "epic_description": (
                    "Implementation of system-level gateway "
                    "and operational requirements."
                ),
                "feature_title": "System Gateway",
                "feature_description": (
                    "Deliver system-level performance and "
                    "availability functionality."
                ),
                "module_id": "MOD-GATEWAY",
                "base_hours": 8,
                "base_points": 3,
                "known_capability": True,
            }

        # Structured fields receive stronger weights.
        scores = []

        for rule in self.CAPABILITY_RULES:

            score = 0

            # Target object is the strongest evidence.
            for pattern in rule["patterns"]:
                if re.search(
                    pattern,
                    target,
                    re.IGNORECASE,
                ):
                    score += 10

            # Action is also strong evidence.
            for pattern in rule["patterns"]:
                if re.search(
                    pattern,
                    action,
                    re.IGNORECASE,
                ):
                    score += 8

            # Summary is strong but slightly weaker.
            for pattern in rule["patterns"]:
                if re.search(
                    pattern,
                    summary,
                    re.IGNORECASE,
                ):
                    score += 6

            # Description is weak evidence.
            for pattern in rule["patterns"]:
                if re.search(
                    pattern,
                    description,
                    re.IGNORECASE,
                ):
                    score += 1

            if score > 0:
                scores.append(
                    (score, rule)
                )

        if scores:

            scores.sort(
                key=lambda item: (
                    item[0],
                    item[1]["base_points"],
                ),
                reverse=True,
            )

            # ----------------------------------------------------------
            # Semantic disambiguation
            # ----------------------------------------------------------

            normalized_action = action.lower().strip()
            normalized_summary = summary.lower()
            normalized_description = description.lower()

            # ----------------------------------------------------------
            # Cross-domain data retention / auditability.
            #
            # Requirements covering retention of multiple domain records
            # are data-management concerns even when incidental payment
            # terms such as "invoice" are present.
            #
            # Requirements describing traceable records across multiple
            # operational domains are reporting/auditability concerns,
            # even when "payment state" is one of the covered domains.
            # ----------------------------------------------------------

            cross_domain_text = (
                normalized_summary
                + " "
                + normalized_description
            )

            cross_domain_retention = (
                re.search(
                    r"\b(?:retention|retain(?:ed|ing)?|retained)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:audit|auditing|auditability|reporting)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:charging sessions?|reservations?|"
                    r"maintenance records?|invoices?|"
                    r"multiple domain|all records?)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
            )

            cross_domain_auditability = (
                re.search(
                    r"\b(?:auditability|audit|traceable record|"
                    r"traceable records|traceability)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:reservation|charging[- ]session|"
                    r"payment|maintenance|administrative|"
                    r"state transition|state transitions)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
                and re.search(
                    r"\b(?:every|each|all|traceable|"
                    r"state transition|state transitions)\b",
                    cross_domain_text,
                    re.IGNORECASE,
                )
            )

            if cross_domain_retention:
                data_rule = next(
                    (
                        rule
                        for rule in self.CAPABILITY_RULES
                        if rule["key"] == "file"
                    ),
                    None,
                )

                # Data Store is an architecture concern rather than a
                # generic file-management capability. Return a synthetic
                # classification that resolves to the existing
                # Application Data Store architecture module.
                return {
                    "key": "data-retention",
                    "epic_key": "data-management",
                    "feature_key": "data-retention",
                    "epic_title": "Data Management",
                    "epic_description": (
                        "Implementation of requirements related to "
                        "application data management."
                    ),
                    "feature_title": "Data Retention",
                    "feature_description": (
                        "Deliver functionality required for data "
                        "retention and auditability."
                    ),
                    "module_id": "MOD-DATA",
                    "base_hours": 10,
                    "base_points": 3,
                    "known_capability": True,
                }

            if cross_domain_auditability:
                reporting_rule = next(
                    (
                        rule
                        for rule in self.CAPABILITY_RULES
                        if rule["key"] == "reporting"
                    ),
                    None,
                )

                if reporting_rule:
                    best_rule = reporting_rule

                    return {
                        "key": best_rule["key"],
                        "epic_key": best_rule["epic_key"],
                        "feature_key": best_rule["key"],
                        "epic_title": best_rule["epic_title"],
                        "epic_description": (
                            f"Implementation of requirements related to "
                            f"{best_rule['epic_title'].lower()}."
                        ),
                        "feature_title": best_rule["feature_title"],
                        "feature_description": (
                            f"Deliver functionality required for "
                            f"{best_rule['feature_title'].lower()}."
                        ),
                        "module_id": best_rule["module_id"],
                        "base_hours": best_rule["base_hours"],
                        "base_points": best_rule["base_points"],
                        "known_capability": True,
                    }

            # ----------------------------------------------------------
            # Operational fault/issue reporting is a maintenance action.
            #
            # Phrases such as "report a faulty charger" or
            # "report a station issue" describe submitting an operational
            # fault, not generating/consuming an analytical report.
            # Keep this narrow so genuine reporting requirements continue
            # to use the Reporting capability.
            # ----------------------------------------------------------

            operational_fault_reporting = re.search(
                r"\breport\b[^.\n]{0,80}"
                r"\b(?:faulty charger|charger fault|charger issue|"
                r"station issue|station fault|charging fault|"
                r"charging issue|charger problem|station problem)\b",
                normalized_summary + " " + normalized_description,
                re.IGNORECASE,
            )

            if operational_fault_reporting:
                maintenance_rule = next(
                    (
                        item[1]
                        for item in scores
                        if item[1]["key"] == "maintenance"
                    ),
                    None,
                )

                if maintenance_rule:
                    best_rule = maintenance_rule

                    return {
                        "key": best_rule["key"],
                        "epic_key": best_rule["epic_key"],
                        "feature_key": best_rule["key"],
                        "epic_title": best_rule["epic_title"],
                        "epic_description": (
                            f"Implementation of requirements related to "
                            f"{best_rule['epic_title'].lower()}."
                        ),
                        "feature_title": best_rule["feature_title"],
                        "feature_description": (
                            f"Deliver functionality required for "
                            f"{best_rule['feature_title'].lower()}."
                        ),
                        "module_id": best_rule["module_id"],
                        "base_hours": best_rule["base_hours"],
                        "base_points": best_rule["base_points"],
                        "known_capability": True,
                    }

            # ----------------------------------------------------------
            # Explicit notification intent.
            #
            # A requirement whose actual action is "notify" should not
            # be classified as Reporting merely because its target is
            # represented as "reports".
            # ----------------------------------------------------------

            if (
                re.search(
                    r"\b(notify|notifies|notified|notifying|notification|notifications)\b",
                    normalized_action,
                )
                and any(
                    item[1]["key"] == "notification"
                    for item in scores
                )
            ):
                notification_rule = next(
                    item[1]
                    for item in scores
                    if item[1]["key"] == "notification"
                )

                reporting_only_report_target = (
                    re.search(
                        r"^\s*reports?\s*$",
                        target,
                        re.IGNORECASE,
                    )
                    and not re.search(
                        r"\bgenerate|view|create|produce|analytics|statistics|metrics\b",
                        normalized_action + " " + normalized_summary,
                        re.IGNORECASE,
                    )
                )

                if reporting_only_report_target:
                    best_rule = notification_rule
                else:
                    best_rule = scores[0][1]

            # ----------------------------------------------------------
            # Explicit access-control intent.
            #
            # Requirements stating that a user can "only access"
            # their own records are authorization requirements even if
            # the generic capability scorer has no authentication hit.
            # ----------------------------------------------------------

            elif re.search(
                r"\b(only access|access control|access restriction)\b"
                r"|\bown (?:data|records|reservations|sessions|invoices|history)\b",
                normalized_summary + " " + normalized_description,
                re.IGNORECASE,
            ):
                authentication_rule = next(
                    (
                        rule
                        for rule in self.CAPABILITY_RULES
                        if rule["key"] == "authentication"
                    ),
                    None,
                )

                if authentication_rule:
                    best_rule = authentication_rule
                else:
                    best_rule = scores[0][1]

            else:
                best_rule = scores[0][1]

            return {
                "key": best_rule["key"],
                "epic_key": best_rule["epic_key"],
                "feature_key": best_rule["key"],
                "epic_title": best_rule["epic_title"],
                "epic_description": (
                    f"Implementation of requirements related to "
                    f"{best_rule['epic_title'].lower()}."
                ),
                "feature_title": best_rule["feature_title"],
                "feature_description": (
                    f"Deliver functionality required for "
                    f"{best_rule['feature_title'].lower()}."
                ),
                "module_id": best_rule["module_id"],
                "base_hours": best_rule["base_hours"],
                "base_points": best_rule["base_points"],
                "known_capability": True,
            }

        # ----------------------------------------------------------
        # Generic domain requirement.
        # ----------------------------------------------------------

        concept = self._generic_concept(
            req
        )

        if concept:

            slug = self._slug(
                concept
            )

            return {
                "key": f"domain-{slug}",
                "epic_key": f"domain-{slug}",
                "feature_key": f"domain-{slug}",
                "epic_title": (
                    f"{self._title_case(concept)} Management"
                ),
                "epic_description": (
                    f"Implementation of application functionality "
                    f"related to {concept}."
                ),
                "feature_title": (
                    f"{self._title_case(concept)} Operations"
                ),
                "feature_description": (
                    f"Implement operations required for {concept}."
                ),
                "module_id": (
                    f"MOD-DOMAIN-{slug.upper()}"
                ),
                "base_hours": 8,
                "base_points": 3,
                "known_capability": False,
            }

        # ----------------------------------------------------------
        # Last-resort general functionality.
        # ----------------------------------------------------------

        return {
            "key": "general-application",
            "epic_key": "general-application",
            "feature_key": "general-functionality",
            "epic_title": "Application Functionality",
            "epic_description": (
                "Implementation of application functionality "
                "identified in the requirements."
            ),
            "feature_title": "General Application Functionality",
            "feature_description": (
                "Implement requirement-specific behavior."
            ),
            "module_id": "MOD-DATA",
            "base_hours": 8,
            "base_points": 3,
            "known_capability": False,
        }

    # ================================================================
    # Architecture module resolution
    # ================================================================

    def _resolve_architecture_module_id(
        self,
        logical_module_id: Optional[str],
        modules: List[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Resolve a logical classifier module ID (e.g. "MOD-AUTHENTICATION")
        to the actual project-scoped architecture module ID supplied by
        the architecture agent (e.g. "3B669A31-MOD-AUTHENTICATION").

        This NEVER fabricates an architecture module. If no real module
        can be matched, it returns None.
        """

        if not logical_module_id:
            return None

        if not modules:
            return None

        logical_module_id = str(logical_module_id).strip()

        if not logical_module_id:
            return None

        # A) Exact ID match.
        for module in modules:
            actual_id = str(module.get("id") or "").strip()
            if actual_id and actual_id == logical_module_id:
                return actual_id

        # B) Project-scoped ID match: actual ID ends with
        # "-<logical_module_id>" (e.g. "3B669A31-MOD-AUTHENTICATION"
        # for logical "MOD-AUTHENTICATION").
        suffix = f"-{logical_module_id}"
        for module in modules:
            actual_id = str(module.get("id") or "").strip()
            if actual_id and actual_id.upper().endswith(suffix.upper()):
                return actual_id

        # C) Reasonable normalized module-name fallback.
        name_part = logical_module_id
        if name_part.upper().startswith("MOD-"):
            name_part = name_part[4:]
        if name_part.upper().startswith("DOMAIN-"):
            name_part = name_part[len("DOMAIN-"):]

        normalized_logical = self._normalize_module_text(name_part)

        if normalized_logical and len(normalized_logical) >= 3:
            for module in modules:
                name = module.get("name")
                if not name:
                    continue

                normalized_name = self._normalize_module_text(
                    str(name)
                )

                if not normalized_name:
                    continue

                # Exact normalized name, singular/plural stem, or exact word token match
                name_words = re.findall(r"[a-z0-9]+", str(name).lower())
                name_stems = {w.rstrip("s") for w in name_words if len(w) > 3}
                logical_stem = normalized_logical.rstrip("s") if len(normalized_logical) > 3 else normalized_logical
                if (
                    normalized_logical == normalized_name
                    or logical_stem == normalized_name.rstrip("s")
                    or normalized_logical in name_words
                    or logical_stem in name_stems
                ):
                    actual_id = str(module.get("id") or "").strip()
                    if actual_id:
                        return actual_id

        # F) No real architecture module matches.
        return None

    @staticmethod
    def _normalize_module_text(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.lower())

    @staticmethod
    def _logical_module_suffix(module_id: Optional[str]) -> str:
        """
        Reduce a possibly project-scoped module ID (e.g.
        "3B669A31-MOD-ORDER") to its logical suffix ("MOD-ORDER") for
        dependency comparisons. Plain logical IDs pass through unchanged.
        """

        if not module_id:
            return ""

        module_id = str(module_id).strip().upper()

        match = re.search(r"(MOD-[A-Z0-9\-]+)$", module_id)

        if match:
            return match.group(1)

        return module_id

    # ================================================================
    # Generic concept
    # ================================================================

    def _generic_concept(
        self,
        req: Dict[str, Any],
    ) -> str:

        target = self._field_text(
            req.get("target_object")
        )

        if not target:
            return ""

        target = re.sub(
            r"^(the|a|an|their|his|her|our|your)\s+",
            "",
            target,
            flags=re.IGNORECASE,
        )

        target = re.sub(
            r"\s+(for|from|with|by|in|on|at|to|of|and|or)\s+.*$",
            "",
            target,
            flags=re.IGNORECASE,
        )

        target = re.sub(
            r"[.,;:!?()\[\]{}]",
            "",
            target,
        )

        target = re.sub(
            r"\s+",
            " ",
            target,
        ).strip()

        if not target:
            return ""

        if len(target.split()) > 4:
            return ""

        return target

    # ================================================================
    # Task details
    # ================================================================

    def _task_title(
        self,
        req: Dict[str, Any],
        classification: Dict[str, Any],
    ) -> str:

        summary = self._field_text(
            req.get("summary")
        )

        if summary:
            return f"Implement: {summary}"

        return (
            f"Implement {classification['feature_title']}"
        )

    def _task_description(
        self,
        req: Dict[str, Any],
        classification: Dict[str, Any],
    ) -> str:

        req_id = req.get(
            "id",
            "requirement",
        )

        summary = self._field_text(
            req.get("summary")
        )

        return (
            f"Implement the behavior specified by "
            f"{req_id}: {summary}. "
            f"This work belongs to the "
            f"{classification['feature_title']} feature "
            f"and uses architecture module "
            f"{classification['module_id']}."
        )

    @staticmethod
    def _generate_subtasks(
        req: Dict[str, Any],
    ) -> List[str]:

        target = str(
            req.get("target_object")
            or "the required functionality"
        ).strip()

        return [
            f"Define or update the data model for {target}",
            f"Implement application logic for {target}",
            f"Expose the required API behavior for {target}",
            "Implement relevant frontend or integration behavior",
            f"Write automated tests for requirement {req.get('id', '')}",
        ]

    # ================================================================
    # Estimation
    # ================================================================

    def _estimate_complexity(
        self,
        req: Dict[str, Any],
        classification: Dict[str, Any],
    ) -> str:

        text = self._field_text(
            req.get("summary")
        ).lower()

        description = self._field_text(
            req.get("description")
        ).lower()

        combined = (
            f"{text} {description}"
        )

        integration_terms = [
            "external",
            "third-party",
            "gateway",
            "webhook",
            "integration",
            "real-time",
            "concurrent",
            "synchron",
        ]

        complexity_score = 0

        complexity_score += sum(
            1
            for term in integration_terms
            if term in combined
        ) * 2

        operation_terms = [
            "create",
            "update",
            "delete",
            "search",
            "filter",
            "process",
            "calculate",
            "upload",
            "download",
            "notify",
        ]

        complexity_score += sum(
            1
            for term in operation_terms
            if re.search(
                rf"\b{re.escape(term)}\w*\b",
                combined,
            )
        )

        if complexity_score >= 5:
            return "high"

        if complexity_score >= 2:
            return "medium"

        return "low"

    @staticmethod
    def _estimate_effort(
        classification: Dict[str, Any],
        complexity: str,
    ):

        base_hours = classification[
            "base_hours"
        ]

        base_points = classification[
            "base_points"
        ]

        if complexity == "high":
            return (
                float(base_hours + 6),
                max(5, base_points),
            )

        if complexity == "medium":
            return (
                float(base_hours),
                max(3, base_points),
            )

        return (
            float(round(base_hours * 0.7, 1)),
            min(3, max(1, base_points)),
        )

    # ================================================================
    # Dependencies
    # ================================================================

    def _generate_dependencies(
        self,
        tasks: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
    ) -> None:

        # Cart -> Order
        for task in tasks:

            task_module = self._logical_module_suffix(
                task["module_id"]
            )

            if task_module == "MOD-ORDER":

                prerequisite = self._previous_task(
                    tasks,
                    task["id"],
                    {"MOD-CART"},
                )

                if prerequisite:
                    self._add_dependency(
                        task,
                        prerequisite,
                        dependencies,
                    )

            # Order -> Payment
            elif task_module == "MOD-PAYMENT":

                prerequisite = self._previous_task(
                    tasks,
                    task["id"],
                    {"MOD-ORDER"},
                )

                if prerequisite:
                    self._add_dependency(
                        task,
                        prerequisite,
                        dependencies,
                    )

            # Operational capability -> notification
            elif task_module == "MOD-NOTIFICATION":

                prerequisite = self._previous_task(
                    tasks,
                    task["id"],
                    {
                        "MOD-ORDER",
                        "MOD-PAYMENT",
                        "MOD-BOOKING",
                        "MOD-ATTENDANCE",
                    },
                )

                if prerequisite:
                    self._add_dependency(
                        task,
                        prerequisite,
                        dependencies,
                    )

    @classmethod
    def _previous_task(
        cls,
        tasks: List[Dict[str, Any]],
        current_id: str,
        module_ids: set,
    ):

        current_number = int(
            current_id.split("-")[1]
        )

        for task in tasks:
            task_number = int(
                task["id"].split("-")[1]
            )

            if task_number >= current_number:
                continue

            if cls._logical_module_suffix(
                task["module_id"]
            ) in module_ids:
                return task

        return None

    @staticmethod
    def _add_dependency(
        task: Dict[str, Any],
        prerequisite: Dict[str, Any],
        dependencies: List[Dict[str, Any]],
    ):

        if prerequisite["id"] in task["depends_on"]:
            return

        task["depends_on"].append(
            prerequisite["id"]
        )

        dependencies.append(
            {
                "task_id": task["id"],
                "depends_on_task_id": prerequisite["id"],
                "dependency_type": "blocks",
            }
        )

    # ================================================================
    # Utilities
    # ================================================================

    @staticmethod
    def _field_text(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(value, list):
            return " ".join(
                str(item)
                for item in value
            )

        if isinstance(value, dict):
            return " ".join(
                str(item)
                for item in value.values()
            )

        return re.sub(
            r"\s+",
            " ",
            str(value),
        ).strip()

    @staticmethod
    def _normalize_priority(
        priority: Any,
    ) -> str:

        value = str(
            priority or "medium"
        ).lower().strip()

        if value in {
            "critical",
            "high",
            "medium",
            "low",
        }:
            return value

        return "medium"

    @staticmethod
    def _sprint_for_task(
        task_number: int,
    ) -> str:

        if task_number <= 6:
            return "Sprint 1"

        if task_number <= 12:
            return "Sprint 2"

        return "Sprint 3"

    @staticmethod
    def _slug(
        value: str,
    ) -> str:

        return re.sub(
            r"[^a-z0-9]+",
            "-",
            value.lower(),
        ).strip("-")

    @staticmethod
    def _title_case(
        value: str,
    ) -> str:

        return " ".join(
            word.capitalize()
            for word in value.split()
        )

    def _derive_required_skills(
        self,
        classification: Dict[str, Any],
        modules: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Derive required skills from the architecture module associated
        with the task.

        Skills are based only on evidence explicitly present in:
        - module name
        - tech_stack
        - responsibilities

        No domain-specific technology is invented.
        """

        module_id = classification.get("module_id")

        if not module_id or not modules:
            return []

        module = next(
            (
                module
                for module in modules
                if str(module.get("id")) == str(module_id)
            ),
            None,
        )

        if not module:
            return []

        evidence_parts: List[str] = []

        name = module.get("name")
        if name:
            evidence_parts.append(str(name))

        tech_stack = module.get("tech_stack")
        if tech_stack:
            evidence_parts.append(str(tech_stack))

        responsibilities = module.get("responsibilities")

        if isinstance(responsibilities, list):
            evidence_parts.extend(
                str(item)
                for item in responsibilities
                if item
            )
        elif responsibilities:
            evidence_parts.append(
                str(responsibilities)
            )

        evidence = " ".join(evidence_parts).lower()

        skills: List[str] = []

        def add(skill: str) -> None:
            if skill not in skills:
                skills.append(skill)

        # Technical capabilities explicitly supported
        # by architecture evidence.

        if (
            "api" in evidence
            or "endpoint" in evidence
            or "application api" in evidence
        ):
            add("API Development")

        if (
            "relational" in evidence
            or "database" in evidence
            or "data access" in evidence
            or "data store" in evidence
        ):
            add("Relational Database")

        if (
            "authentication" in evidence
            or "authorization" in evidence
            or "credentials" in evidence
            or "access control" in evidence
        ):
            add("Authentication & Authorization")

        if (
            "notification" in evidence
            or "alert" in evidence
            or "email" in evidence
            or "message" in evidence
        ):
            add("Notification Systems")

        if (
            "gateway" in evidence
            or "reverse proxy" in evidence
        ):
            add("API Gateway")

        if (
            "search" in evidence
            or "filter" in evidence
        ):
            add("Search & Filtering")

        if (
            "payment" in evidence
            or "transaction" in evidence
        ):
            add("Payment Processing")

        if (
            "report" in evidence
            or "analytics" in evidence
        ):
            add("Reporting & Analytics")

        if (
            "file" in evidence
            or "document" in evidence
            or "upload" in evidence
        ):
            add("File & Document Management")

        return skills