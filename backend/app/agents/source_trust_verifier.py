import re
from typing import List, Dict, Any, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SourceTrustVerifier:
    """
    Automated Source-Trust / Source-Alignment Verifier.

    Purpose:
        Evaluate whether extracted requirements remain grounded in the
        client document.

    IMPORTANT:
        This verifier does NOT claim conventional accuracy, precision,
        recall, or F1.

        It produces a transparent source-alignment / trust score based
        on deterministic checks:

            1. Evidence Support
            2. Semantic Alignment
            3. Constraint Preservation
            4. Source Coverage Consistency
            5. Unsupported Content

    It is designed for arbitrary client documents and does not require
    a predefined requirement count or manually authored ground truth.

    The score is an internal source-alignment measure, NOT ground-truth
    accuracy.
    """

    # Fixed weights.
    #
    # These weights should remain fixed for an evaluation run rather than
    # being tuned to obtain a desired score.
    EVIDENCE_WEIGHT = 0.30
    SEMANTIC_WEIGHT = 0.25
    CONSTRAINT_WEIGHT = 0.25
    COVERAGE_WEIGHT = 0.20

    # Semantic similarity threshold used when independently matching
    # source sentences to extracted requirements.
    SOURCE_MATCH_THRESHOLD = 0.45

    # Stronger threshold for considering a source statement directly
    # supported by an extracted requirement.
    STRONG_SOURCE_MATCH_THRESHOLD = 0.60

    def __init__(self) -> None:
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            ngram_range=(1, 2),
            min_df=1,
        )

    # =================================================================
    # PUBLIC API
    # =================================================================

    def verify(
        self,
        source_chunks: List[Dict[str, Any]],
        requirements: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Verify extracted requirements against the source document.

        Parameters:
            source_chunks:
                IngestionAgent chunks.

            requirements:
                Extracted requirement dictionaries.

        Returns:
            Dictionary containing:
                - overall_score
                - component scores
                - requirement-level verification
                - coverage details
                - summary
        """

        source_text = self._build_source_text(
            source_chunks
        )

        if not source_text.strip():
            return self._empty_result(
                reason="No source text was available."
            )

        source_statements = self._extract_source_statements(
            source_text
        )

        if not source_statements:
            return self._empty_result(
                reason="No requirement-bearing source statements were detected."
            )

        requirement_results = []

        for requirement in requirements:

            result = self._verify_requirement(
                requirement,
                source_text,
                source_statements,
            )

            requirement_results.append(
                result
            )

        # -------------------------------------------------------------
        # Aggregate requirement-level scores.
        # -------------------------------------------------------------

        if requirement_results:

            evidence_support = self._average(
                [
                    result["evidence_support_pct"]
                    for result in requirement_results
                ]
            )

            semantic_alignment = self._average(
                [
                    result["semantic_alignment_pct"]
                    for result in requirement_results
                ]
            )

            constraint_preservation = self._average(
                [
                    result["constraint_preservation_pct"]
                    for result in requirement_results
                ]
            )

            unsupported_content = self._average(
                [
                    result["unsupported_content_pct"]
                    for result in requirement_results
                ]
            )

        else:

            evidence_support = 0.0
            semantic_alignment = 0.0
            constraint_preservation = 0.0
            unsupported_content = 0.0

        # -------------------------------------------------------------
        # Independent source coverage.
        # -------------------------------------------------------------

        coverage_result = self._calculate_source_coverage(
            source_statements,
            requirement_results
        )

        coverage_consistency = (
            coverage_result["coverage_consistency_pct"]
        )

        # -------------------------------------------------------------
        # Overall score.
        #
        # Unsupported content is treated as a penalty.
        #
        # We first calculate the positive source-alignment score and
        # then subtract a limited unsupported-content penalty.
        # -------------------------------------------------------------

        base_score = (
            (
                evidence_support
                * self.EVIDENCE_WEIGHT
            )
            + (
                semantic_alignment
                * self.SEMANTIC_WEIGHT
            )
            + (
                constraint_preservation
                * self.CONSTRAINT_WEIGHT
            )
            + (
                coverage_consistency
                * self.COVERAGE_WEIGHT
            )
        )

        unsupported_penalty = (
            unsupported_content * 0.10
        )

        overall_score = max(
            0.0,
            min(
                100.0,
                base_score - unsupported_penalty
            )
        )

        # -------------------------------------------------------------
        # Verification status.
        # -------------------------------------------------------------

        status = self._status_from_score(
            overall_score,
            unsupported_content
        )

        supported_count = sum(
            1
            for result in requirement_results
            if result["evidence_support_pct"] >= 100.0
        )

        strong_semantic_count = sum(
            1
            for result in requirement_results
            if result["semantic_alignment_pct"] >= 80.0
        )

        constraint_count = sum(
            1
            for result in requirement_results
            if result["constraint_preservation_pct"] >= 90.0
        )

        return {
            "overall_score": round(
                overall_score,
                2
            ),
            "status": status,

            "evidence_support_pct": round(
                evidence_support,
                2
            ),

            "semantic_alignment_pct": round(
                semantic_alignment,
                2
            ),

            "constraint_preservation_pct": round(
                constraint_preservation,
                2
            ),

            "coverage_consistency_pct": round(
                coverage_consistency,
                2
            ),

            "unsupported_content_pct": round(
                unsupported_content,
                2
            ),

            "requirements_total": len(
                requirements
            ),

            "requirements_with_direct_evidence": (
                supported_count
            ),

            "requirements_with_strong_semantic_match": (
                strong_semantic_count
            ),

            "requirements_with_preserved_constraints": (
                constraint_count
            ),

            "source_statements_detected": len(
                source_statements
            ),

            "source_statements_supported": (
                coverage_result[
                    "source_statements_supported"
                ]
            ),

            "uncovered_source_statements": (
                coverage_result[
                    "uncovered_source_statements"
                ]
            ),

            "requirements": requirement_results,

            "methodology": {
                "evidence_weight": self.EVIDENCE_WEIGHT,
                "semantic_weight": self.SEMANTIC_WEIGHT,
                "constraint_weight": self.CONSTRAINT_WEIGHT,
                "coverage_weight": self.COVERAGE_WEIGHT,
                "semantic_match_threshold": (
                    self.SOURCE_MATCH_THRESHOLD
                ),
                "strong_semantic_match_threshold": (
                    self.STRONG_SOURCE_MATCH_THRESHOLD
                ),
                "note": (
                    "This is an automated source-alignment "
                    "and trustworthiness measure, not "
                    "ground-truth accuracy."
                ),
            },
        }

    # =================================================================
    # SOURCE CONSTRUCTION
    # =================================================================

    @staticmethod
    def _build_source_text(
        source_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Reconstruct the complete source document from ingestion chunks.
        """

        ordered_chunks = sorted(
            source_chunks,
            key=lambda chunk: (
                chunk.get(
                    "chunk_index",
                    0
                )
            )
        )

        parts = []

        for chunk in ordered_chunks:

            content = str(
                chunk.get(
                    "content",
                    ""
                )
            ).strip()

            if content:
                parts.append(
                    content
                )

        return "\n\n".join(
            parts
        )

    # =================================================================
    # SOURCE STATEMENT EXTRACTION
    # =================================================================

    def _extract_source_statements(
        self,
        source_text: str
    ) -> List[str]:
        """
        Independently split the source into candidate statements.

        This is intentionally separate from ExtractionAgent.

        The purpose is to provide an independent coverage signal rather
        than simply trusting the extracted requirement list.
        """

        normalized = re.sub(
            r"[ \t]+",
            " ",
            source_text
        )

        normalized = re.sub(
            r"\s*\n\s*",
            " ",
            normalized
        )

        raw_statements = re.split(
            r"(?<=[.!?])\s+",
            normalized
        )

        statements = []

        for statement in raw_statements:

            cleaned = statement.strip()

            if not cleaned:
                continue

            cleaned = re.sub(
                r"^\[Page\s+\d+\]\s*",
                "",
                cleaned,
                flags=re.IGNORECASE
            )

            cleaned = re.sub(
                r"^\d+(?:\.\d+)*[\.)]\s*",
                "",
                cleaned
            )

            cleaned = re.sub(
                r"^[-*•]+\s*",
                "",
                cleaned
            )

            cleaned = cleaned.strip()

            if len(cleaned) < 20:
                continue

            if self._is_heading_or_noise(
                cleaned
            ):
                continue

            if not self._looks_requirement_bearing(
                cleaned
            ):
                continue

            statements.append(
                cleaned
            )

        # Exact deduplication.
        unique = []
        seen = set()

        for statement in statements:

            key = self._normalize(
                statement
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(
                statement
            )

        return unique

    @staticmethod
    def _looks_requirement_bearing(
        text: str
    ) -> bool:
        """
        Detect likely requirement-bearing statements.

        This is deliberately broader than a strict requirement parser,
        because the verifier needs to detect source statements that the
        extractor may have missed.
        """

        lower = text.lower()

        patterns = [
            r"\bmust\b",
            r"\bshall\b",
            r"\bshould\b",
            r"\bcan\b",
            r"\bwill\b",
            r"\bneeds?\s+to\b",
            r"\brequired\s+to\b",
            r"\ballows?\b",
            r"\benables?\b",
            r"\bprovides?\b",
            r"\bsupports?\b",
            r"\bmanage\b",
            r"\bmanages\b",
            r"\bcreate\b",
            r"\bcreates\b",
            r"\bview\b",
            r"\bsubmit\b",
            r"\brecord\b",
            r"\bupload\b",
            r"\bmodify\b",
            r"\bdelete\b",
            r"\baccess\b",
            r"\bstore\b",
            r"\bstored\b",
            r"\bgenerate\b",
            r"\bgenerates\b",
            r"\bavailable\b",
            r"\bsecure\b",
            r"\brole-based\b",
            r"\b24/7\b",
            r"\bpermanently\b",
        ]

        return any(
            re.search(
                pattern,
                lower
            )
            for pattern in patterns
        )

    @staticmethod
    def _is_heading_or_noise(
        text: str
    ) -> bool:

        stripped = text.strip()

        if not stripped:
            return True

        if (
            len(stripped) < 80
            and stripped.isupper()
        ):
            return True

        heading_patterns = [
            r"^\d+(?:\.\d+)*\s+[A-Z][A-Za-z ]+$",
            r"^(overview|introduction|"
            r"student requirements|faculty requirements|"
            r"administrator requirements|"
            r"authentication and security|"
            r"notifications|ai assistant|"
            r"performance|availability|reporting|"
            r"important policy|data retention)$",
        ]

        return any(
            re.match(
                pattern,
                stripped,
                flags=re.IGNORECASE
            )
            for pattern in heading_patterns
        )

    # =================================================================
    # REQUIREMENT-LEVEL VERIFICATION
    # =================================================================

    def _verify_requirement(
        self,
        requirement: Dict[str, Any],
        source_text: str,
        source_statements: List[str],
    ) -> Dict[str, Any]:
        """
        Verify one extracted requirement.
        """

        requirement_id = str(
            requirement.get(
                "id",
                ""
            )
        )

        summary = str(
            requirement.get(
                "summary",
                ""
            )
        ).strip()

        description = str(
            requirement.get(
                "description",
                ""
            )
        ).strip()

        source_excerpt = str(
            requirement.get(
                "source_excerpt",
                ""
            )
        ).strip()

        generated_text = " ".join(
            part
            for part in [
                summary,
                description,
            ]
            if part
        )

        # -------------------------------------------------------------
        # 1. Evidence support
        # -------------------------------------------------------------

        evidence_exact = (
            source_excerpt in source_text
            if source_excerpt
            else False
        )

        evidence_normalized = False

        if source_excerpt:
            evidence_normalized = (
                self._normalize(
                    source_excerpt
                )
                in self._normalize(
                    source_text
                )
            )

        if evidence_exact:
            evidence_support = 100.0
            evidence_method = "exact_source_match"

        elif evidence_normalized:
            evidence_support = 100.0
            evidence_method = "normalized_source_match"

        elif source_excerpt:
            evidence_support = 0.0
            evidence_method = "source_excerpt_not_found"

        else:
            evidence_support = 0.0
            evidence_method = "missing_source_excerpt"

        # -------------------------------------------------------------
        # 2. Semantic alignment
        # -------------------------------------------------------------

        semantic_score, semantic_source, semantic_similarity = (
            self._semantic_alignment(
                generated_text,
                source_excerpt,
                source_statements
            )
        )

        # -------------------------------------------------------------
        # 3. Constraint preservation
        # -------------------------------------------------------------

        constraint_result = (
            self._constraint_preservation(
                source_excerpt,
                generated_text
            )
        )

        # -------------------------------------------------------------
        # 4. Unsupported content
        # -------------------------------------------------------------

        unsupported_result = (
            self._unsupported_content(
                generated_text,
                source_excerpt,
                semantic_similarity
            )
        )

        return {
            "requirement_id": requirement_id,

            "summary": summary,

            "evidence_support_pct": round(
                evidence_support,
                2
            ),

            "evidence_method": evidence_method,

            "semantic_alignment_pct": round(
                semantic_score,
                2
            ),

            "semantic_match_source": semantic_source,

            "constraint_preservation_pct": round(
                constraint_result[
                    "score_pct"
                ],
                2
            ),

            "constraints_source": (
                constraint_result[
                    "source_constraints"
                ]
            ),

            "constraints_preserved": (
                constraint_result[
                    "preserved_constraints"
                ]
            ),

            "constraints_missing": (
                constraint_result[
                    "missing_constraints"
                ]
            ),

            "unsupported_content_pct": round(
                unsupported_result[
                    "unsupported_pct"
                ],
                2
            ),

            "unsupported_content_flags": (
                unsupported_result[
                    "flags"
                ]
            ),

            "source_excerpt": source_excerpt,

            "verification_status": (
                self._requirement_status(
                    evidence_support,
                    semantic_score,
                    constraint_result[
                        "score_pct"
                    ],
                    unsupported_result[
                        "unsupported_pct"
                    ]
                )
            ),
        }

    # =================================================================
    # SEMANTIC ALIGNMENT
    # =================================================================

    def _semantic_alignment(
        self,
        generated_text: str,
        source_excerpt: str,
        source_statements: List[str],
    ) -> Tuple[float, str, float]:
        """
        Calculate semantic alignment using TF-IDF cosine similarity.

        This is intentionally local/deterministic.

        It is not a pretrained semantic embedding model, so the score
        should be interpreted as lexical/semantic similarity rather than
        deep language understanding.
        """

        if not generated_text.strip():
            return 0.0, "", 0.0

        comparison_sources = []

        if source_excerpt.strip():
            comparison_sources.append(
                source_excerpt
            )

        comparison_sources.extend(
            source_statements
        )

        if not comparison_sources:
            return 0.0, "", 0.0

        documents = [
            generated_text
        ] + comparison_sources

        try:
            matrix = self.vectorizer.fit_transform(
                documents
            )

            similarities = cosine_similarity(
                matrix[0:1],
                matrix[1:]
            )[0]

        except Exception:
            return 0.0, "", 0.0

        if len(similarities) == 0:
            return 0.0, "", 0.0

        best_index = int(
            similarities.argmax()
        )

        best_similarity = float(
            similarities[best_index]
        )

        best_source = comparison_sources[
            best_index
        ]

        # Source excerpt gets priority when it exists and has a strong
        # match, because it is the requirement's claimed evidence.
        if source_excerpt.strip():

            try:
                excerpt_index = comparison_sources.index(
                    source_excerpt
                )

                excerpt_similarity = float(
                    similarities[
                        excerpt_index
                    ]
                )

                if (
                    excerpt_similarity
                    >= best_similarity * 0.90
                ):
                    best_similarity = (
                        excerpt_similarity
                    )
                    best_source = source_excerpt

            except ValueError:
                pass

        return (
            max(
                0.0,
                min(
                    100.0,
                    best_similarity * 100.0
                )
            ),
            best_source,
            best_similarity,
        )

    # =================================================================
    # CONSTRAINT PRESERVATION
    # =================================================================

    def _constraint_preservation(
        self,
        source_text: str,
        generated_text: str,
    ) -> Dict[str, Any]:
        """
        Check preservation of explicit constraints.

        Examples:

            24/7
            two years
            before the deadline
            after publication
            permanently
            only
            anytime
            thousands of users

        This is a conservative check based on explicit source
        constraint markers.

        If the source contains no detectable constraint, the score is
        100 because there is no detected constraint to preserve.
        """

        source_constraints = (
            self._extract_constraints(
                source_text
            )
        )

        if not source_constraints:
            return {
                "score_pct": 100.0,
                "source_constraints": [],
                "preserved_constraints": [],
                "missing_constraints": [],
            }

        generated_normalized = self._normalize(
            generated_text
        )

        preserved = []
        missing = []

        for constraint in source_constraints:

            variants = constraint[
                "variants"
            ]

            if any(
                variant in generated_normalized
                for variant in variants
            ):
                preserved.append(
                    constraint["display"]
                )
            else:
                missing.append(
                    constraint["display"]
                )

        score = (
            len(preserved)
            / len(source_constraints)
        ) * 100.0

        return {
            "score_pct": score,
            "source_constraints": [
                constraint["display"]
                for constraint in source_constraints
            ],
            "preserved_constraints": preserved,
            "missing_constraints": missing,
        }

    def _extract_constraints(
        self,
        text: str
    ) -> List[Dict[str, Any]]:
        """
        Extract explicit constraint markers from source text.
        """

        normalized = self._normalize(
            text
        )

        constraints = []

        # -------------------------------------------------------------
        # Numeric constraints
        # -------------------------------------------------------------

        for match in re.finditer(
            r"\b\d+(?:\.\d+)?\s*(?:%|years?|months?|days?|hours?|"
            r"minutes?|seconds?)\b",
            normalized,
            flags=re.IGNORECASE
        ):
            value = match.group(0).strip()

            constraints.append(
                {
                    "display": value,
                    "variants": {
                        value,
                        value.replace(
                            " ",
                            ""
                        ),
                    },
                }
            )

        # -------------------------------------------------------------
        # 24/7
        # -------------------------------------------------------------

        if (
            "24/7" in normalized
            or "24 7" in normalized
        ):
            constraints.append(
                {
                    "display": "24/7",
                    "variants": {
                        "24/7",
                        "24 7",
                        "twenty four seven",
                    },
                }
            )

        # -------------------------------------------------------------
        # Temporal / conditional phrases
        # -------------------------------------------------------------

        temporal_patterns = [
            (
                r"\bbefore the deadline\b",
                "before the deadline"
            ),
            (
                r"\bafter the deadline\b",
                "after the deadline"
            ),
            (
                r"\bafter (?:the )?semester\b",
                "after semester"
            ),
            (
                r"\bafter .*?results? are published\b",
                "after results are published"
            ),
            (
                r"\bwhenever necessary\b",
                "whenever necessary"
            ),
            (
                r"\bat any time\b",
                "at any time"
            ),
            (
                r"\banytime\b",
                "anytime"
            ),
            (
                r"\bimmediately\b",
                "immediately"
            ),
            (
                r"\breal[- ]time\b",
                "real-time"
            ),
        ]

        for pattern, display in temporal_patterns:

            if re.search(
                pattern,
                normalized
            ):
                constraints.append(
                    {
                        "display": display,
                        "variants": {
                            display,
                            display.replace(
                                "-",
                                " "
                            ),
                        },
                    }
                )

        # -------------------------------------------------------------
        # Quantifiers / restrictions
        # -------------------------------------------------------------

        restriction_patterns = [
            (
                r"\bonly\b",
                "only"
            ),
            (
                r"\bpermanently\b",
                "permanently"
            ),
            (
                r"\bsecurely\b",
                "securely"
            ),
            (
                r"\bsecure\b",
                "secure"
            ),
            (
                r"\bthousands of (?:students?|users?)\b",
                "thousands of users"
            ),
        ]

        for pattern, display in restriction_patterns:

            if re.search(
                pattern,
                normalized
            ):
                constraints.append(
                    {
                        "display": display,
                        "variants": {
                            display,
                        },
                    }
                )

        # -------------------------------------------------------------
        # Deduplicate overlapping constraints.
        # -------------------------------------------------------------

        unique = []
        seen = set()

        for constraint in constraints:

            key = constraint["display"]

            if key in seen:
                continue

            seen.add(key)
            unique.append(
                constraint
            )

        return unique

    # =================================================================
    # UNSUPPORTED CONTENT
    # =================================================================

    def _unsupported_content(
        self,
        generated_text: str,
        source_excerpt: str,
        semantic_similarity: float,
    ) -> Dict[str, Any]:
        """
        Estimate unsupported generated content.

        This is intentionally conservative.

        It does NOT claim that every paraphrased word must occur in the
        source.

        It flags stronger warning signals:

            - missing source evidence
            - very low source similarity
            - generated numeric facts absent from source
            - generated temporal facts absent from source
            - generated strong restrictions absent from source

        This is a risk indicator, not a perfect hallucination detector.
        """

        flags = []

        if not source_excerpt.strip():
            flags.append(
                "No source excerpt was supplied."
            )

            return {
                "unsupported_pct": 100.0,
                "flags": flags,
            }

        # -------------------------------------------------------------
        # Low semantic alignment.
        # -------------------------------------------------------------

        if (
            semantic_similarity
            < self.SOURCE_MATCH_THRESHOLD
        ):
            flags.append(
                "Generated requirement has low "
                "similarity to its cited source."
            )

        # -------------------------------------------------------------
        # Numeric facts.
        # -------------------------------------------------------------

        generated_numbers = set(
            re.findall(
                r"\b\d+(?:\.\d+)?\s*(?:%|years?|months?|days?|"
                r"hours?|minutes?|seconds?)?\b",
                self._normalize(
                    generated_text
                ),
                flags=re.IGNORECASE
            )
        )

        source_numbers = set(
            re.findall(
                r"\b\d+(?:\.\d+)?\s*(?:%|years?|months?|days?|"
                r"hours?|minutes?|seconds?)?\b",
                self._normalize(
                    source_excerpt
                ),
                flags=re.IGNORECASE
            )
        )

        for number in generated_numbers:

            normalized_number = number.strip()

            if (
                normalized_number
                and normalized_number
                not in source_numbers
            ):
                flags.append(
                    f"Generated numeric fact not found "
                    f"in cited source: {normalized_number}"
                )

        # -------------------------------------------------------------
        # Explicit high-impact constraints.
        # -------------------------------------------------------------

        generated_constraints = (
            self._extract_constraints(
                generated_text
            )
        )

        source_constraint_text = (
            self._normalize(
                source_excerpt
            )
        )

        for constraint in generated_constraints:

            variants = constraint[
                "variants"
            ]

            if not any(
                variant in source_constraint_text
                for variant in variants
            ):
                flags.append(
                    "Generated constraint not found "
                    f"in cited source: "
                    f"{constraint['display']}"
                )

        # -------------------------------------------------------------
        # Convert flags to a conservative percentage.
        # -------------------------------------------------------------

        if not flags:
            unsupported_pct = 0.0

        else:
            # Each flag contributes 20 percentage points, capped at 100.
            unsupported_pct = min(
                100.0,
                len(flags) * 20.0
            )

        return {
            "unsupported_pct": unsupported_pct,
            "flags": flags,
        }

    # =================================================================
    # INDEPENDENT SOURCE COVERAGE
    # =================================================================

    def _calculate_source_coverage(
        self,
        source_statements: List[str],
        requirement_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Independently compare requirement-bearing source statements
        against extracted requirements.

        This is called coverage consistency rather than recall because
        there is no independently labeled ground-truth set.
        """

        if not source_statements:
            return {
                "coverage_consistency_pct": 0.0,
                "source_statements_supported": 0,
                "uncovered_source_statements": [],
            }

        extracted_texts = []

        for result in requirement_results:

            excerpt = result.get(
                "source_excerpt",
                ""
            )

            summary = result.get(
                "summary",
                ""
            )

            if excerpt:
                extracted_texts.append(
                    excerpt
                )
            elif summary:
                extracted_texts.append(
                    summary
                )

        if not extracted_texts:
            return {
                "coverage_consistency_pct": 0.0,
                "source_statements_supported": 0,
                "uncovered_source_statements": (
                    source_statements
                ),
            }

        # -------------------------------------------------------------
        # Build one TF-IDF corpus containing source statements and
        # extracted source evidence.
        # -------------------------------------------------------------

        documents = (
            source_statements
            + extracted_texts
        )

        try:
            matrix = self.vectorizer.fit_transform(
                documents
            )

            source_matrix = matrix[
                :len(source_statements)
            ]

            extracted_matrix = matrix[
                len(source_statements):
            ]

            similarity_matrix = cosine_similarity(
                source_matrix,
                extracted_matrix
            )

        except Exception:

            return {
                "coverage_consistency_pct": 0.0,
                "source_statements_supported": 0,
                "uncovered_source_statements": (
                    source_statements
                ),
            }

        supported = 0
        uncovered = []

        for index, statement in enumerate(
            source_statements
        ):

            similarities = similarity_matrix[
                index
            ]

            if len(similarities) == 0:
                uncovered.append(
                    statement
                )
                continue

            best_similarity = float(
                similarities.max()
            )

            if (
                best_similarity
                >= self.STRONG_SOURCE_MATCH_THRESHOLD
            ):
                supported += 1
            else:
                uncovered.append(
                    statement
                )

        coverage = (
            supported
            / len(source_statements)
        ) * 100.0

        return {
            "coverage_consistency_pct": coverage,
            "source_statements_supported": supported,
            "uncovered_source_statements": uncovered,
        }

    # =================================================================
    # STATUS HELPERS
    # =================================================================

    @staticmethod
    def _requirement_status(
        evidence: float,
        semantic: float,
        constraints: float,
        unsupported: float,
    ) -> str:

        if (
            evidence >= 100
            and semantic >= 80
            and constraints >= 90
            and unsupported <= 10
        ):
            return "verified"

        if (
            evidence >= 100
            and semantic >= 60
            and constraints >= 70
            and unsupported <= 30
        ):
            return "mostly_supported"

        return "needs_review"

    @staticmethod
    def _status_from_score(
        score: float,
        unsupported_content: float,
    ) -> str:

        if (
            score >= 90
            and unsupported_content <= 5
        ):
            return "high_source_alignment"

        if (
            score >= 75
            and unsupported_content <= 20
        ):
            return "source_aligned_with_review"

        if score >= 60:
            return "mixed_source_alignment"

        return "low_source_alignment"

    # =================================================================
    # GENERAL HELPERS
    # =================================================================

    @staticmethod
    def _normalize(
        text: str
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            str(text)
        ).strip().lower()

    @staticmethod
    def _average(
        values: List[float]
    ) -> float:

        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _empty_result(
        reason: str
    ) -> Dict[str, Any]:

        return {
            "overall_score": 0.0,
            "status": "not_evaluable",

            "evidence_support_pct": 0.0,
            "semantic_alignment_pct": 0.0,
            "constraint_preservation_pct": 0.0,
            "coverage_consistency_pct": 0.0,
            "unsupported_content_pct": 0.0,

            "requirements_total": 0,
            "requirements_with_direct_evidence": 0,
            "requirements_with_strong_semantic_match": 0,
            "requirements_with_preserved_constraints": 0,

            "source_statements_detected": 0,
            "source_statements_supported": 0,
            "uncovered_source_statements": [],

            "requirements": [],

            "methodology": {
                "note": (
                    "Verification could not be evaluated."
                ),
                "reason": reason,
            },
        }