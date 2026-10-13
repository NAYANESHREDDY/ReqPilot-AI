import re
from typing import List, Dict, Any

from backend.app.agents.llm_adapter import LLMAdapter


class ExtractionAgent:
    """
    Requirement Extraction Agent.

    Hybrid requirement extraction agent.

    LLM mode:
        Uses controlled two-pass extraction:

        Pass 1:
            Identify genuine requirement-bearing statements across the
            complete document using bounded batches.

        Pass 2:
            Convert discovered candidates into structured requirements.

    Deterministic mode:
        Uses the rule-based fallback when no LLM is configured or when
        the LLM extraction process fails.

    Design priorities:
        1. Requirement quality
        2. Source fidelity
        3. Document coverage
        4. Meaningful requirement boundaries
        5. Zero hallucination
        6. Accurate provenance
    """

    def __init__(self, llm_adapter: LLMAdapter):
        self.llm = llm_adapter

    async def extract_requirements(
        self,
        chunks: List[Dict[str, Any]],
        source_doc_id: str
    ) -> List[Dict[str, Any]]:

        # -------------------------------------------------------------
        # Build complete source context.
        # -------------------------------------------------------------
        valid_chunks = [
            chunk
            for chunk in chunks
            if chunk.get("content")
        ]

        combined_text = "\n\n".join(
            [
                (
                    f"[Page {chunk.get('page_number', 1)}]\n"
                    f"{chunk.get('content', '')}"
                )
                for chunk in valid_chunks
            ]
        )

        if not combined_text.strip():
            return []

        # -------------------------------------------------------------
        # DETERMINISTIC SOURCE-COVERAGE BASELINE
        # -------------------------------------------------------------
        # The deterministic extractor establishes stable requirement
        # coverage from the client document BEFORE the LLM runs.
        # This prevents stochastic LLM output from changing the
        # requirement count for the same source document.
        deterministic_results = self._extract_deterministic(
            chunks,
            source_doc_id
        )

        # -------------------------------------------------------------
        # REAL LLM EXTRACTION / SEMANTIC ENRICHMENT
        # -------------------------------------------------------------
        # The LLM improves the structured fields, but it is NOT the
        # authority for source coverage.
        if self.llm.api_key:
            llm_results = await self._extract_with_llm(
                combined_text,
                source_doc_id
            )

            if llm_results:
                return self._merge_llm_with_deterministic_coverage(
                    llm_results,
                    deterministic_results
                )

        return deterministic_results

    # =================================================================
    # CONTROLLED-BATCH TWO-PASS LLM EXTRACTION
    # =================================================================

    async def _extract_with_llm(
        self,
        text: str,
        source_doc_id: str
    ) -> List[Dict[str, Any]]:
        """
        Controlled-batch source-grounded LLM extraction.

        The complete document is processed in bounded batches instead of
        being truncated at an arbitrary character limit.

        Pass 1:
            Discover complete requirement-bearing statements across
            every batch.

        Pass 2:
            Convert discovered candidates into structured requirements.

        Every final source excerpt is validated against the complete
        original document before being accepted.
        """

        # -------------------------------------------------------------
        # CONTROLLED BATCH SIZE
        # -------------------------------------------------------------
        MAX_BATCH_CHARS = 12000

        def build_batches(source_text: str) -> List[str]:
            """
            Split the complete source into bounded text batches.

            Paragraph boundaries are preferred so that sentences and
            requirement statements are not unnecessarily split.
            """

            paragraphs = [
                block.strip()
                for block in re.split(
                    r"\n\s*\n",
                    source_text
                )
                if block.strip()
            ]

            if not paragraphs:
                if source_text.strip():
                    return [source_text[:MAX_BATCH_CHARS]]
                return []

            batches = []
            current_parts = []
            current_length = 0

            for paragraph in paragraphs:

                paragraph_length = len(paragraph)

                # -----------------------------------------------------
                # Handle unusually large paragraphs.
                # -----------------------------------------------------
                if paragraph_length > MAX_BATCH_CHARS:

                    if current_parts:
                        batches.append(
                            "\n\n".join(current_parts)
                        )
                        current_parts = []
                        current_length = 0

                    # Prefer sentence boundaries when possible.
                    sentences = re.split(
                        r"(?<=[.!?])\s+",
                        paragraph
                    )

                    sentence_parts = []
                    sentence_length = 0

                    for sentence in sentences:
                        sentence = sentence.strip()

                        if not sentence:
                            continue

                        sentence_len = len(sentence)

                        if (
                            sentence_parts
                            and sentence_length + sentence_len + 1
                            > MAX_BATCH_CHARS
                        ):
                            batches.append(
                                "\n".join(sentence_parts)
                            )
                            sentence_parts = []
                            sentence_length = 0

                        # A single enormous sentence must still be split.
                        if sentence_len > MAX_BATCH_CHARS:
                            if sentence_parts:
                                batches.append(
                                    "\n".join(sentence_parts)
                                )
                                sentence_parts = []
                                sentence_length = 0

                            for start in range(
                                0,
                                sentence_len,
                                MAX_BATCH_CHARS
                            ):
                                batches.append(
                                    sentence[
                                        start:start + MAX_BATCH_CHARS
                                    ]
                                )
                        else:
                            sentence_parts.append(sentence)
                            sentence_length += (
                                sentence_len
                                if not sentence_parts[:-1]
                                else sentence_len + 1
                            )

                    if sentence_parts:
                        batches.append(
                            "\n".join(sentence_parts)
                        )

                    continue

                additional_length = (
                    paragraph_length
                    if not current_parts
                    else paragraph_length + 2
                )

                # -----------------------------------------------------
                # Start a new batch when current batch is full.
                # -----------------------------------------------------
                if (
                    current_parts
                    and current_length + additional_length
                    > MAX_BATCH_CHARS
                ):
                    batches.append(
                        "\n\n".join(current_parts)
                    )

                    current_parts = []
                    current_length = 0

                current_parts.append(paragraph)
                current_length += additional_length

            if current_parts:
                batches.append(
                    "\n\n".join(current_parts)
                )

            return batches

        # -------------------------------------------------------------
        # Sanitize the complete document.
        #
        # IMPORTANT:
        # There is deliberately NO arbitrary [:16000] truncation.
        # -------------------------------------------------------------
        safe_full_text = self.llm.sanitize_untrusted_input(text)

        batches = build_batches(safe_full_text)

        if not batches:
            return []

        # =============================================================
        # PASS 1: REQUIREMENT COVERAGE DISCOVERY
        # =============================================================

        all_candidates = []

        for batch_index, batch_text in enumerate(
            batches,
            start=1
        ):

            discovery_prompt = f"""
You are a senior software requirements analyst.

You are processing batch {batch_index} of {len(batches)} from a
software requirements document.

Analyze THIS ENTIRE BATCH carefully.

Your task is to identify genuine, complete requirement-bearing
statements contained in this batch.

============================================================
OBJECTIVE
============================================================

Find meaningful software requirements describing:

- functional capabilities
- user actions
- system behavior
- authentication
- authorization
- registration
- verification
- profile management
- password management
- session management
- notifications
- data handling
- security
- privacy
- API/interface behavior
- performance
- availability
- reliability
- scalability
- usability
- compliance
- explicit business rules
- explicit policy constraints
- other explicit software constraints

Do not assume that every document contains every category.

============================================================
CRITICAL REQUIREMENT BOUNDARY RULES
============================================================

A requirement must represent a COMPLETE engineering statement.

A requirement may span multiple physical lines or paragraphs.

Physical line breaks DO NOT define requirement boundaries.

Before creating a candidate, reconstruct the complete source statement
from adjacent lines when the source clearly continues the same sentence,
clause, list, condition, or requirement.

DO NOT split one requirement merely because:

- the sentence wraps onto another line
- a list continues onto another line
- a clause follows a comma
- a condition follows the main statement
- the source formatting wraps text
- a sentence continues after a page/line break

Examples:

SOURCE:
"Students should be able to log in securely and view their enrolled
courses, attendance, assignments, examination schedules, results, and
campus notifications."

This is ONE requirement.

SOURCE:
"The system should provide an AI-powered assistant that answers
academic and campus-related questions."

This is ONE requirement.

SOURCE:
"Attendance records should become permanently locked after
the semester examination results are published."

This is ONE requirement.

SOURCE:
"The system should be available 24/7."

This is ONE requirement.

DO NOT produce fragments such as:

- "courses, attendance, assignments..."
- "academic and campus-related questions."
- "the semester examination results are published."
- "student activity."
- "after the semester examination results are published."

A continuation clause is NOT an independent requirement unless the
source explicitly presents it as an independent obligation.

============================================================
INDEPENDENT REQUIREMENTS
============================================================

Clearly independent capabilities should remain separate.

For example:

"Faculty members should create and manage courses."

and

"Faculty members should record student attendance."

are two independent requirements.

Do not merge genuinely independent requirements merely because they
have the same actor.

============================================================
DOCUMENT NOISE
============================================================

Do NOT return:

- document titles
- project names
- section headings
- table-of-contents entries
- page labels
- author information
- general background
- introductory context
- explanatory prose without a concrete system obligation
- standalone list fragments
- continuation clauses
- sentence fragments

============================================================
SOURCE GROUNDING
============================================================

Every candidate MUST be directly supported by the source.

Do NOT invent requirements.

For every candidate provide:

- concise candidate summary
- exact verbatim source excerpt
- page number if explicitly available

The source excerpt MUST be copied exactly.

Do not paraphrase source_excerpt.

The source_excerpt should normally contain the COMPLETE requirement
statement, including important conditions, constraints, qualifiers,
and continuation clauses.

============================================================
COVERAGE
============================================================

Inspect the ENTIRE batch.

Do not stop after finding the first few requirements.

Do not optimize for a specific number of candidates.

Return every genuine complete requirement-bearing statement supported
by this batch.

============================================================
BATCH {batch_index}
============================================================

{batch_text}
"""

            discovery_schema = """{
  "candidates": [
    {
      "summary": "Short description of the complete requirement",
      "source_page": 1,
      "source_excerpt": "Exact verbatim complete requirement text from the document"
    }
  ]
}

STRICT RULES:

- Return only genuine complete requirements.
- Do not return headings or project descriptions.
- Do not target a particular number of candidates.
- Do not duplicate candidates.
- Preserve meaningful requirement boundaries.
- A requirement may span multiple physical lines.
- Reconstruct continuation lines before creating a candidate.
- Do not return sentence fragments.
- Do not return continuation clauses as separate requirements.
- source_excerpt MUST be verbatim.
- source_excerpt SHOULD contain the complete requirement statement.
- Preserve important conditions and qualifiers.
- source_page must correspond to the source when page information exists.
"""

            discovery_data = await self.llm.generate_json(
                discovery_prompt,
                discovery_schema
            )

            if not discovery_data:
                continue

            candidates = discovery_data.get(
                "candidates",
                []
            )

            if not isinstance(candidates, list):
                continue

            for candidate in candidates:

                if not isinstance(candidate, dict):
                    continue

                summary = str(
                    candidate.get(
                        "summary",
                        ""
                    )
                ).strip()

                excerpt = str(
                    candidate.get(
                        "source_excerpt",
                        ""
                    )
                ).strip()

                page = self._safe_page_number(
                    candidate.get("source_page")
                )

                if not summary or not excerpt:
                    continue

                # -----------------------------------------------------
                # CRITICAL PROVENANCE CHECK
                # -----------------------------------------------------
                if not self._source_excerpt_exists(
                    excerpt,
                    text
                ):
                    continue

                # -----------------------------------------------------
                # CRITICAL REQUIREMENT-BOUNDARY CHECK
                #
                # Reject obvious continuation fragments before they
                # reach Pass 2.
                # -----------------------------------------------------
                if self._looks_like_fragment(excerpt):
                    continue

                all_candidates.append(
                    {
                        "summary": summary,
                        "source_page": page,
                        "source_excerpt": excerpt,
                    }
                )

        # -------------------------------------------------------------
        # No candidates discovered.
        # -------------------------------------------------------------
        if not all_candidates:
            return []

        # =============================================================
        # REMOVE DUPLICATE DISCOVERY CANDIDATES
        # =============================================================

        unique_candidates = []
        seen_excerpts = set()

        for candidate in all_candidates:

            key = self._normalize_for_match(
                candidate["source_excerpt"]
            )

            if not key:
                continue

            if key in seen_excerpts:
                continue

            seen_excerpts.add(key)

            unique_candidates.append(
                candidate
            )

        if not unique_candidates:
            return []

        # =============================================================
        # PASS 2: STRUCTURED REQUIREMENT EXTRACTION
        # =============================================================

        MAX_CANDIDATE_BATCH_CHARS = 10000

        candidate_batches = []
        current_candidates = []
        current_length = 0

        for candidate in unique_candidates:

            candidate_block = (
                f"Summary: {candidate['summary']}\n"
                f"Page: {candidate['source_page']}\n"
                f"Exact Source: {candidate['source_excerpt']}"
            )

            candidate_length = len(candidate_block)

            if (
                current_candidates
                and current_length + candidate_length
                > MAX_CANDIDATE_BATCH_CHARS
            ):
                candidate_batches.append(
                    current_candidates
                )

                current_candidates = []
                current_length = 0

            current_candidates.append(
                candidate
            )

            current_length += candidate_length

        if current_candidates:
            candidate_batches.append(
                current_candidates
            )

        structured_results = []

        for candidate_batch in candidate_batches:

            candidate_text = "\n\n".join(
                [
                    (
                        f"Candidate {index + 1}:\n"
                        f"Summary: {candidate['summary']}\n"
                        f"Page: {candidate['source_page']}\n"
                        f"Exact Source: {candidate['source_excerpt']}"
                    )
                    for index, candidate in enumerate(
                        candidate_batch
                    )
                ]
            )

            structured_prompt = f"""
You are a senior software requirements engineer.

Convert the following source-grounded requirement candidates into
high-quality structured software requirements.

============================================================
MOST IMPORTANT RULE
============================================================

Preserve the requirement meaning from the source.

Do NOT invent behavior.

Do NOT add implementation details that are not present in the source.

Do NOT add assumptions merely to make the requirement appear more
complete.

============================================================
REQUIREMENT BOUNDARIES
============================================================

Each candidate should normally become ONE structured requirement.

However, before producing the result, verify that the candidate itself
represents a COMPLETE requirement.

Never create a requirement from:

- a sentence fragment
- a continuation clause
- a list continuation
- a dependent condition
- a noun phrase
- the second half of another requirement

If a candidate contains a complete requirement statement with multiple
clauses, preserve those clauses together.

Do not split:

"Attendance records should become permanently locked after the
semester examination results are published."

into two requirements.

Do not split:

"Students should be able to log in securely and view their enrolled
courses, attendance, assignments, examination schedules, results, and
campus notifications."

into multiple requirements.

============================================================
CANDIDATE COVERAGE
============================================================

Normally produce one structured requirement for each genuine complete
candidate.

Reject a candidate ONLY when it is clearly:

- document noise
- a heading
- a duplicate
- background information
- a sentence fragment
- a continuation clause
- not actually a software requirement

Do not discard a valid complete requirement simply because it is short.

Do not merge clearly independent capabilities.

============================================================
REQUIREMENT TYPE
============================================================

Use ONLY:

"functional"
"non_functional"

Use "functional" for system capabilities and behavior.

Use "non_functional" for:

- security
- API/interface constraints
- performance
- availability
- reliability
- scalability
- usability
- privacy
- compliance
- other quality or technical constraints

============================================================
STRUCTURED FIELDS
============================================================

For every valid requirement produce:

summary:
A concise meaningful requirement title.

description:
A faithful description of the complete source requirement.

actor:
The actor explicitly supported by the source.
Use "System" when system behavior is described without a human actor.

action:
The primary action supported by the source.

target_object:
The entity/resource affected by the action.

preconditions:
ONLY conditions explicitly supported by the source.
Do not automatically add authentication or authorization.

expected_outcome:
ONLY the outcome supported by the source.

acceptance_criteria:
Concise Given/When/Then criteria.
They MUST NOT introduce new behavior.

priority:
Choose high, medium, or low based on the wording and importance
expressed by the source.

confidence:
A value from 0.0 to 1.0 reflecting confidence that the requirement
is directly supported by the source.

source_page:
Use the candidate page.

source_excerpt:
Copy the candidate source excerpt EXACTLY.

============================================================
SOURCE-GROUNDING RULE
============================================================

Every structured requirement must correspond to one of the candidates.

Do not create additional requirements.

Do not invent facts.

Do not split a candidate into multiple requirements unless the
candidate explicitly contains clearly independent requirements and
the source itself clearly separates them.

============================================================
CANDIDATES
============================================================

{candidate_text}
"""

            structured_schema = """{
  "requirements": [
    {
      "id": "FR-001",
      "req_type": "functional",
      "summary": "Short meaningful requirement title",
      "description": "Faithful complete requirement description",
      "actor": "User",
      "action": "perform source-supported action",
      "target_object": "source-supported entity",
      "preconditions": "",
      "expected_outcome": "Only the source-supported outcome",
      "acceptance_criteria": [
        "Given only a source-supported condition, When the source-supported action occurs, Then the source-supported outcome occurs"
      ],
      "priority": "medium",
      "confidence": 0.95,
      "source_page": 2,
      "source_excerpt": "Exact verbatim complete source text"
    }
  ]
}

STRICT RULES:

- Use only functional or non_functional.
- Do not invent requirements.
- Do not invent implementation details.
- Do not invent preconditions.
- Do not invent outcomes.
- Do not invent acceptance behavior.
- Do not duplicate requirements.
- Preserve meaningful requirement boundaries.
- Do not split continuation clauses.
- Do not convert fragments into requirements.
- source_excerpt MUST be verbatim.
- source_excerpt MUST represent the complete requirement.
- source_page MUST correspond to the candidate.
"""

            structured_data = await self.llm.generate_json(
                structured_prompt,
                structured_schema
            )

            if not structured_data:
                continue

            results = structured_data.get(
                "requirements",
                []
            )

            if not isinstance(results, list):
                continue

            structured_results.extend(
                results
            )

        if not structured_results:
            return []

        # =============================================================
        # VALIDATE STRUCTURED RESULTS
        # =============================================================

        validated_results = []

        for requirement in structured_results:

            if not isinstance(requirement, dict):
                continue

            required_fields = [
                "req_type",
                "summary",
                "description",
                "actor",
                "action",
                "target_object",
                "preconditions",
                "expected_outcome",
                "acceptance_criteria",
                "priority",
                "confidence",
                "source_page",
                "source_excerpt",
            ]

            if not all(
                field in requirement
                for field in required_fields
            ):
                continue

            # ---------------------------------------------------------
            # Normalize requirement type.
            # ---------------------------------------------------------

            req_type = str(
                requirement.get(
                    "req_type",
                    ""
                )
            ).strip().lower()

            if req_type == "functional":
                requirement["req_type"] = "functional"
            elif req_type == "non_functional":
                requirement["req_type"] = "non_functional"
            else:
                continue

            # ---------------------------------------------------------
            # Normalize text fields.
            # ---------------------------------------------------------

            for field in [
                "summary",
                "description",
                "actor",
                "action",
                "target_object",
                "preconditions",
                "expected_outcome",
                "source_excerpt",
            ]:
                requirement[field] = str(
                    requirement.get(
                        field,
                        ""
                    )
                ).strip()

            if not requirement["summary"]:
                continue

            if not requirement["description"]:
                continue

            if not requirement["source_excerpt"]:
                continue

            # ---------------------------------------------------------
            # Validate source excerpt against COMPLETE document.
            # ---------------------------------------------------------

            if not self._source_excerpt_exists(
                requirement["source_excerpt"],
                text
            ):
                continue

            # ---------------------------------------------------------
            # Reject obvious fragments in Pass 2 as well.
            # ---------------------------------------------------------

            if self._looks_like_fragment(
                requirement["source_excerpt"]
            ):
                continue

            # ---------------------------------------------------------
            # Normalize page.
            # ---------------------------------------------------------

            requirement["source_page"] = (
                self._safe_page_number(
                    requirement.get(
                        "source_page"
                    )
                )
            )

            # ---------------------------------------------------------
            # Normalize acceptance criteria.
            # ---------------------------------------------------------

            acceptance = requirement.get(
                "acceptance_criteria",
                []
            )

            if isinstance(
                acceptance,
                str
            ):
                acceptance = [
                    acceptance
                ]

            if not isinstance(
                acceptance,
                list
            ):
                acceptance = []

            requirement["acceptance_criteria"] = [
                str(item).strip()
                for item in acceptance
                if str(item).strip()
            ]

            # ---------------------------------------------------------
            # Normalize priority.
            # ---------------------------------------------------------

            priority = str(
                requirement.get(
                    "priority",
                    "medium"
                )
            ).strip().lower()

            if priority not in {
                "high",
                "medium",
                "low",
            }:
                priority = "medium"

            requirement["priority"] = priority

            # ---------------------------------------------------------
            # Normalize confidence.
            # ---------------------------------------------------------

            try:
                confidence = float(
                    requirement.get(
                        "confidence",
                        0.5
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                confidence = 0.5

            requirement["confidence"] = max(
                0.0,
                min(
                    1.0,
                    confidence
                )
            )

            # ---------------------------------------------------------
            # Application-controlled metadata.
            # ---------------------------------------------------------

            requirement["source_id"] = (
                source_doc_id
            )

            requirement["status"] = (
                "needs_review"
            )

            requirement["is_ai_suggested"] = (
                True
            )

            validated_results.append(
                requirement
            )

        # =============================================================
        # EXACT DUPLICATE REMOVAL
        # =============================================================

        unique_results = []
        seen = set()

        for requirement in validated_results:

            key = (
                requirement["req_type"],
                self._normalize_for_match(
                    requirement[
                        "source_excerpt"
                    ]
                ),
            )

            if key in seen:
                continue

            seen.add(key)

            unique_results.append(
                requirement
            )

        # =============================================================
        # ADDITIONAL CONTAINMENT DEDUPLICATION
        #
        # If one source excerpt is completely contained inside another
        # longer source excerpt, prefer the longer complete statement.
        #
        # This helps remove cases where an LLM returns both:
        #
        #   "records should become locked"
        #
        # and:
        #
        #   "records should become permanently locked after results..."
        #
        # The longer source-grounded statement is retained.
        # =============================================================

        unique_results = self._remove_contained_source_duplicates(
            unique_results
        )

        # =============================================================
        # STABLE APPLICATION-OWNED IDS
        # =============================================================

        functional_counter = 1
        nfr_counter = 1

        for requirement in unique_results:

            if requirement["req_type"] == "functional":

                requirement["id"] = (
                    f"FR-{functional_counter:03d}"
                )

                functional_counter += 1

            else:

                requirement["id"] = (
                    f"NFR-{nfr_counter:03d}"
                )

                nfr_counter += 1

        return unique_results

    # =================================================================
    # DETERMINISTIC COVERAGE + LLM ENRICHMENT MERGE
    # =================================================================

    def _merge_llm_with_deterministic_coverage(
        self,
        llm_results: List[Dict[str, Any]],
        deterministic_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge LLM semantic enrichment onto a deterministic source-coverage
        baseline.

        The deterministic extractor is the coverage authority.

        Therefore:

        * every deterministic requirement is retained;
        * an LLM requirement is used only when its source excerpt exactly
          matches, or conservatively contains/is contained by, the
          deterministic source excerpt;
        * LLM-only requirements are NOT added;
        * deterministic provenance is always restored;
        * stable application-owned IDs are regenerated after the merge.

        This prevents stochastic LLM responses from changing requirement
        coverage for the same client document.
        """

        if not deterministic_results:
            return []

        if not llm_results:
            return deterministic_results

        merged_results = []

        for deterministic_requirement in deterministic_results:
            deterministic_excerpt = self._normalize_for_match(
                deterministic_requirement.get(
                    "source_excerpt",
                    ""
                )
            )

            if not deterministic_excerpt:
                continue

            best_llm_match = None
            best_match_length = -1

            for llm_requirement in llm_results:
                llm_excerpt = self._normalize_for_match(
                    llm_requirement.get(
                        "source_excerpt",
                        ""
                    )
                )

                if not llm_excerpt:
                    continue

                # Exact source match is strongest.
                if deterministic_excerpt == llm_excerpt:
                    best_llm_match = llm_requirement
                    best_match_length = len(llm_excerpt)
                    break

                # Conservative containment matching.
                if (
                    deterministic_excerpt in llm_excerpt
                    or llm_excerpt in deterministic_excerpt
                ):
                    match_length = min(
                        len(deterministic_excerpt),
                        len(llm_excerpt)
                    )

                    if match_length > best_match_length:
                        best_llm_match = llm_requirement
                        best_match_length = match_length

            if best_llm_match is not None:
                enriched = dict(best_llm_match)

                # Deterministic extraction owns provenance.
                enriched["source_excerpt"] = (
                    deterministic_requirement["source_excerpt"]
                )
                enriched["source_page"] = (
                    deterministic_requirement["source_page"]
                )
                enriched["source_id"] = (
                    deterministic_requirement["source_id"]
                )

                # Application-controlled metadata.
                enriched["status"] = "needs_review"
                enriched["is_ai_suggested"] = True

                merged_results.append(enriched)

            else:
                # LLM missed this requirement.
                # Keep deterministic coverage instead of losing it.
                merged_results.append(
                    dict(deterministic_requirement)
                )

        # Remove containment duplicates after enrichment.
        merged_results = self._remove_contained_source_duplicates(
            merged_results
        )

        # -------------------------------------------------------------
        # Stable application-owned IDs
        # -------------------------------------------------------------
        functional_counter = 1
        nfr_counter = 1

        for requirement in merged_results:

            if requirement["req_type"] == "functional":
                requirement["id"] = (
                    f"FR-{functional_counter:03d}"
                )
                functional_counter += 1

            else:
                requirement["id"] = (
                    f"NFR-{nfr_counter:03d}"
                )
                nfr_counter += 1

        return merged_results

    # =================================================================
    # REQUIREMENT BOUNDARY VALIDATION
    # =================================================================

    @staticmethod
    def _looks_like_fragment(
        text: str
    ) -> bool:
        """
        Detect obvious continuation fragments.

        This is intentionally conservative.

        It rejects common fragments such as:

            "courses, attendance, assignments..."
            "the semester examination results are published."
            "academic performance, course enrollment..."
            "after the semester examination results are published."

        while allowing complete requirements such as:

            "The system should be available 24/7."

            "Students should be able to submit assignments online."

            "Faculty members can modify attendance records."

        This is NOT a grammatical correctness checker. It is only a
        safety filter against obvious requirement fragmentation.
        """

        value = re.sub(
            r"\s+",
            " ",
            str(text)
        ).strip()

        if not value:
            return True

        lower = value.lower()

        # -------------------------------------------------------------
        # Obvious list/continuation starters.
        # -------------------------------------------------------------

        continuation_starters = (
            "and ",
            "or ",
            "but ",
            "after ",
            "before ",
            "when ",
            "while ",
            "because ",
            "which ",
            "that ",
            "including ",
            "such as ",
            "as well as ",
            "along with ",
        )

        if lower.startswith(
            continuation_starters
        ):
            return True

        # -------------------------------------------------------------
        # Lowercase fragments without a requirement-bearing verb.
        #
        # We deliberately allow lowercase complete requirements when
        # they contain a strong requirement pattern.
        # -------------------------------------------------------------

        first_character = value[0]

        requirement_patterns = [
            r"\bmust\b",
            r"\bshall\b",
            r"\bshould\b",
            r"\bcan\b",
            r"\bwill\b",
            r"\bneeds?\s+to\b",
            r"\bis\s+required\s+to\b",
            r"\bare\s+required\s+to\b",
            r"\ballows?\b",
            r"\benables?\b",
            r"\bprovides?\b",
            r"\bsupports?\b",
            r"\bmanages?\b",
            r"\bcreates?\b",
            r"\bupdates?\b",
            r"\bdeletes?\b",
            r"\bgenerates?\b",
            r"\bdisplays?\b",
            r"\bstores?\b",
            r"\bmaintains?\b",
            r"\bensures?\b",
            r"\bprevents?\b",
        ]

        has_requirement_verb = any(
            re.search(
                pattern,
                lower
            )
            for pattern in requirement_patterns
        )

        if first_character.islower() and not has_requirement_verb:
            return True

        # -------------------------------------------------------------
        # Pure list-like fragments.
        #
        # Example:
        #   "courses, attendance, assignments, examination schedules"
        # -------------------------------------------------------------

        words = value.split()

        if (
            len(words) <= 12
            and "," in value
            and not has_requirement_verb
            and not re.search(
                r"[.!?]$",
                value
            )
        ):
            return True

        # -------------------------------------------------------------
        # Very short dependent clauses without a requirement verb.
        # -------------------------------------------------------------

        dependent_prefixes = (
            "the ",
            "this ",
            "these ",
            "those ",
            "student ",
            "students ",
            "faculty ",
            "administrator ",
            "administrators ",
            "user ",
            "users ",
            "academic ",
            "semester ",
        )

        if (
            lower.startswith(dependent_prefixes)
            and not has_requirement_verb
            and not re.search(
                r"[.!?]$",
                value
            )
        ):
            return True

        return False

    @staticmethod
    def _remove_contained_source_duplicates(
        requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove source excerpts that are exact textual subsets of longer
        source excerpts.

        This is conservative and only operates on source text.

        The longer complete source statement is preferred.
        """

        if len(requirements) <= 1:
            return requirements

        normalized = []

        for index, requirement in enumerate(
            requirements
        ):
            excerpt = re.sub(
                r"\s+",
                " ",
                str(
                    requirement.get(
                        "source_excerpt",
                        ""
                    )
                )
            ).strip().lower()

            normalized.append(
                (
                    index,
                    excerpt
                )
            )

        remove_indexes = set()

        for i, (
            index_i,
            text_i
        ) in enumerate(normalized):

            if not text_i:
                continue

            for j, (
                index_j,
                text_j
            ) in enumerate(normalized):

                if i == j:
                    continue

                if not text_j:
                    continue

                if text_i == text_j:
                    continue

                # Only remove if the shorter excerpt is fully contained
                # inside the longer excerpt.
                if (
                    len(text_i) < len(text_j)
                    and text_i in text_j
                ):
                    remove_indexes.add(
                        index_i
                    )
                    break

        return [
            requirement
            for index, requirement in enumerate(
                requirements
            )
            if index not in remove_indexes
        ]

    # =================================================================
    # SOURCE VALIDATION
    # =================================================================

    @staticmethod
    def _normalize_for_match(
        text: str
    ) -> str:
        """
        Normalize whitespace for source matching.
        """

        return re.sub(
            r"\s+",
            " ",
            str(text)
        ).strip().lower()

    def _source_excerpt_exists(
        self,
        excerpt: str,
        source_text: str
    ) -> bool:
        """
        Check whether an LLM-produced excerpt exists in the source.

        Exact matching is attempted first.

        A whitespace-normalized comparison is then attempted so that
        line wrapping or PDF/DOCX extraction whitespace does not cause
        a legitimate source excerpt to be rejected.
        """

        if not excerpt or not source_text:
            return False

        # -------------------------------------------------------------
        # Direct match.
        # -------------------------------------------------------------

        if excerpt in source_text:
            return True

        # -------------------------------------------------------------
        # Whitespace-normalized match.
        # -------------------------------------------------------------

        normalized_excerpt = (
            self._normalize_for_match(
                excerpt
            )
        )

        normalized_source = (
            self._normalize_for_match(
                source_text
            )
        )

        return (
            normalized_excerpt
            in normalized_source
        )

    # =================================================================
    # PAGE NORMALIZATION
    # =================================================================

    @staticmethod
    def _safe_page_number(
        value: Any
    ) -> int:

        try:
            page = int(value)

            if page > 0:
                return page

        except (
            TypeError,
            ValueError
        ):
            pass

        return 1

    # =================================================================
    # DETERMINISTIC FALLBACK
    # =================================================================

    def _extract_deterministic(
        self,
        chunks: List[Dict[str, Any]],
        source_doc_id: str
    ) -> List[Dict[str, Any]]:

        extracted = []

        for chunk in chunks:

            page = chunk.get(
                "page_number",
                1
            )

            content = chunk.get(
                "content",
                ""
            )

            if not content.strip():
                continue

            # ---------------------------------------------------------
            # The deterministic fallback should also preserve complete
            # statements rather than treating every physical line as a
            # separate requirement.
            # ---------------------------------------------------------
            sentences = self._split_sentences(
                content
            )

            for sentence in sentences:

                sentence_clean = sentence.strip()

                if len(sentence_clean) < 15:
                    continue

                if self._looks_like_fragment(
                    sentence_clean
                ):
                    continue

                req_info = self._analyze_sentence(
                    sentence_clean
                )

                if not req_info:
                    continue

                req_type = (
                    "non_functional"
                    if req_info["is_nfr"]
                    else "functional"
                )

                extracted.append(
                    {
                        "id": "",
                        "req_type": req_type,
                        "summary": req_info[
                            "summary"
                        ],
                        "description": sentence_clean,
                        "actor": req_info[
                            "actor"
                        ],
                        "action": req_info[
                            "action"
                        ],
                        "target_object": req_info[
                            "target_object"
                        ],
                        "preconditions": req_info[
                            "preconditions"
                        ],
                        "expected_outcome": req_info[
                            "expected_outcome"
                        ],
                        "acceptance_criteria": req_info[
                            "acceptance_criteria"
                        ],
                        "priority": req_info[
                            "priority"
                        ],
                        "status": "needs_review",
                        "confidence": req_info[
                            "confidence"
                        ],
                        "is_ai_suggested": False,
                        "source_id": source_doc_id,
                        "source_page": page,
                        "source_excerpt": sentence_clean,
                    }
                )

        # -------------------------------------------------------------
        # Remove exact duplicate source statements.
        # -------------------------------------------------------------

        unique = []
        seen = set()

        for requirement in extracted:

            key = (
                requirement["req_type"],
                self._normalize_for_match(
                    requirement["source_excerpt"]
                ),
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(requirement)

        # -------------------------------------------------------------
        # Stable IDs.
        # -------------------------------------------------------------

        fr_counter = 1
        nfr_counter = 1

        for requirement in unique:

            if requirement["req_type"] == "functional":

                requirement["id"] = (
                    f"FR-{fr_counter:03d}"
                )

                fr_counter += 1

            else:

                requirement["id"] = (
                    f"NFR-{nfr_counter:03d}"
                )

                nfr_counter += 1

        return unique

    # =================================================================
    # DETERMINISTIC SENTENCE SPLITTING
    # =================================================================

    def _split_sentences(
        self,
        text: str
    ) -> List[str]:
        """
        Split text into complete statements.

        Physical line breaks are treated as formatting rather than
        automatic requirement boundaries.

        This prevents DOCX/PDF wrapping from creating fragments.
        """

        # -------------------------------------------------------------
        # Normalize line wrapping first.
        # -------------------------------------------------------------
        normalized = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        # Join ordinary line wraps into spaces.
        normalized = re.sub(
            r"\s*\n\s*",
            " ",
            normalized
        )

        # Split on actual sentence-ending punctuation.
        raw_sentences = re.split(
            r"(?<=[.!?])\s+",
            normalized
        )

        result = []

        for sentence in raw_sentences:

            cleaned = re.sub(
                r"^[-*•]+\s*",
                "",
                sentence
            ).strip()

            # Remove numbered-list prefixes only when they are clearly
            # list numbering and not part of the sentence.
            cleaned = re.sub(
                r"^\d+(?:\.\d+)*[\.)]\s*",
                "",
                cleaned
            ).strip()

            if cleaned:
                result.append(
                    cleaned
                )

        return result

    # =================================================================
    # DETERMINISTIC SENTENCE ANALYSIS
    # =================================================================

    def _analyze_sentence(
        self,
        sentence: str
    ) -> Dict[str, Any]:

        lower = sentence.lower()

        # -------------------------------------------------------------
        # NFR indicators
        # -------------------------------------------------------------

        nfr_indicators = [
            "response time",
            "latency",
            "concurrent users",
            "simultaneous users",
            "uptime",
            "availability",
            "security",
            "encryption",
            "throughput",
            "scalable",
            "ssl",
            "tls",
            "fast",
            "compliant",
            "backup",
            "data protection",
            "performance",
            "plaintext",
            "hashing",
            "audit record",
            "audit log",
            "validated on the server",
            "http status",
            "json format",
            "rest api",
            "rest apis",
            "24/7",
            "permanently",
        ]

        is_nfr = any(
            indicator in lower
            for indicator in nfr_indicators
        )

        # -------------------------------------------------------------
        # Requirement indicators
        # -------------------------------------------------------------

        modal_patterns = [
            (
                r"\b("
                r"must|shall|should|needs? to|can|will|"
                r"is required to|are required to|ought to|"
                r"allows?|enables?|provides?|supports?|"
                r"manages?|generates?|displays?|stores?|"
                r"maintains?|ensures?|prevents?"
                r")\b"
            ),
            (
                r"\b("
                r"support|manage|generate|view|track|create|"
                r"update|delete|cancel|book|pay|notify|authenticate|"
                r"submit|record|upload|modify|lock|store"
                r")\b"
            ),
            # ---------------------------------------------------------
            # Additional declarative requirement verbs.
            #
            # These cover statements such as "Students receive ...",
            # "Faculty only access ...", "The assistant answers ...",
            # which have no modal ("should", "can", ...) and use a verb
            # that the patterns above do not contain.
            #
            # Only base / third-person forms are matched (no past
            # tense) so that narrative sentences such as "The team
            # received feedback" are not treated as requirements.
            #
            # "allow" is intentionally NOT added: "allows?" is already
            # covered by the first pattern above.
            # ---------------------------------------------------------
            (
                r"\b("
                r"receives?|sends?|restricts?|retains?|publish(?:es)?"
                r")\b"
            ),
            # "access" and "answer" are also common nouns, so they are
            # matched only when not directly preceded by a determiner
            # or possessive ("the access", "an answer", "their access")
            # and not followed by "control" ("access control").
            (
                r"(?<!\bthe )(?<!\ba )(?<!\ban )(?<!\bno )(?<!\bany )"
                r"(?<!\bits )(?<!\btheir )(?<!\bour )"
                r"\b(?:access(?:es)?|answers?)\b(?!\s+controls?\b)"
            ),
            # Passive obligation with an explicit auxiliary, e.g.
            # "accounts are automatically deleted", "records are
            # stored permanently". The bare-verb patterns above do
            # not match participles ("deleted", "stored", "locked").
            # Limited to a small set of clearly requirement-bearing
            # participles.
            (
                r"\b(?:is|are|be|been)\s+(?:\w+ly\s+)?"
                r"(?:deleted|stored|locked|retained|published|"
                r"restricted|sent|notified)\b"
            ),
        ]

        has_requirement_pattern = any(
            re.search(
                pattern,
                lower
            )
            for pattern in modal_patterns
        )

        if not has_requirement_pattern:
            return None

        # -------------------------------------------------------------
        # Actor
        # -------------------------------------------------------------

        actor = "System"

        actor_match = re.search(
            (
                r"\b("
                r"student|students|faculty|administrator|"
                r"administrators|admin|user|users|customer|"
                r"client|manager|patient|doctor|visitor"
                r")\b"
            ),
            lower
        )

        if actor_match:
            actor = (
                actor_match
                .group(1)
                .capitalize()
            )

        # -------------------------------------------------------------
        # Priority
        # -------------------------------------------------------------

        priority = "medium"

        if any(
            word in lower
            for word in [
                "must",
                "critical",
                "mandatory",
                "essential",
                "secure",
                "immediately",
                "permanently",
                "24/7",
            ]
        ):
            priority = "high"

        elif any(
            word in lower
            for word in [
                "optional",
                "nice to have",
                "future",
                "secondary",
            ]
        ):
            priority = "low"

        # -------------------------------------------------------------
        # Conservative deterministic fields.
        #
        # IMPORTANT:
        # Do not invent authentication, authorization, logging, or
        # success behavior.
        # -------------------------------------------------------------

        action = "perform operation"
        target_obj = "system behavior"

        # -------------------------------------------------------------
        # Lightweight action extraction.
        # -------------------------------------------------------------

        action_match = re.search(
            r"\b("
            r"create|manage|record|upload|modify|view|submit|"
            r"generate|delete|authenticate|notify|provide|"
            r"store|lock|support|display|track|update|"
            r"publish|receive|access"
            r")\b",
            lower
        )

        if action_match:
            action = action_match.group(1)

        # -------------------------------------------------------------
        # Lightweight target extraction.
        # -------------------------------------------------------------

        target_patterns = [
            r"\b(courses?)\b",
            r"\b(attendance(?: records?)?)\b",
            r"\b(assignments?)\b",
            r"\b(examination schedules?)\b",
            r"\b(results?)\b",
            r"\b(notifications?)\b",
            r"\b(reports?)\b",
            r"\b(academic records?)\b",
            r"\b(accounts?)\b",
            r"\b(student records?)\b",
            r"\b(faculty records?)\b",
            r"\b(departments?)\b",
            r"\b(academic performance)\b",
        ]

        for pattern in target_patterns:

            target_match = re.search(
                pattern,
                lower
            )

            if target_match:
                target_obj = target_match.group(1)
                break

        # -------------------------------------------------------------
        # Summary
        # -------------------------------------------------------------

        words = sentence.split()

        if len(words) > 10:

            summary = " ".join(
                words[:10]
            )

            if not summary.endswith("."):
                summary += "..."

        else:
            summary = sentence

        # -------------------------------------------------------------
        # Source-faithful acceptance criteria.
        #
        # We intentionally avoid adding:
        # - authenticated
        # - authorized
        # - logged
        # - recorded
        # - successful execution
        #
        # unless the source itself says so.
        # -------------------------------------------------------------

        acceptance_criteria = [
            (
                "Given the source-stated context, "
                "when the source-stated action occurs, "
                "then the source-stated outcome should occur."
            )
        ]

        # -------------------------------------------------------------
        # Conservative outcome.
        # -------------------------------------------------------------

        expected_outcome = sentence

        return {
            "is_nfr": is_nfr,
            "summary": summary,
            "actor": actor,
            "action": action,
            "target_object": target_obj,
            "preconditions": "",
            "expected_outcome": expected_outcome,
            "acceptance_criteria": acceptance_criteria,
            "priority": priority,
            "confidence": (
                0.90
                if has_requirement_pattern
                else 0.75
            ),
        }