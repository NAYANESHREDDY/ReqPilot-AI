from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class DuplicateAgent:
    """Agent 8.7: Duplicate & Overlap Detection Agent
    Calculates semantic and lexical similarity to identify redundant or overlapping requirements.
    Uses hybrid TF-IDF cosine similarity, token Jaccard overlap,
    and requirement-domain normalization.
    """

    NORMALIZATION_MAP = {
        # Communication / notification
        "dispatched": "send",
        "dispatch": "send",
        "sent": "send",
        "sending": "send",

        # Account lifecycle
        "registration": "account_creation",
        "register": "account_creation",
        "registered": "account_creation",
        "account_creation": "account_creation",
        "account": "account",

        # Timing expressions
        "upon": "after",
        "immediately": "after",
        "shortly": "after",

        # Common requirement wording
        "shall": "",
        "must": "",
        "should": "",
        "system": "",
        "user": "user",
    }

    def _normalize_requirement(self, text: str) -> str:
        """Normalize semantically equivalent requirement vocabulary."""
        text = text.lower()

        # Preserve multi-word concepts before token normalization.
        replacements = {
            "account creation": "account_creation",
            "successful registration": "account_creation",
            "email confirmation": "email_confirmation",
            "email notification": "email_notification",
            "immediately after": "after",
        }

        for source, target in replacements.items():
            text = text.replace(source, target)

        tokens = text.split()
        normalized = []

        for token in tokens:
            token = token.strip(".,;:!?()[]{}\"'")
            if not token:
                continue

            replacement = self.NORMALIZATION_MAP.get(token, token)
            if replacement:
                normalized.append(replacement)

        return " ".join(normalized)

    def detect_duplicates(
        self,
        requirements: List[Dict[str, Any]],
        threshold: float = 0.65
    ) -> List[Dict[str, Any]]:
        if len(requirements) < 2:
            return []

        corpus = [
            f"{r.get('summary', '')} {r.get('description', '')}"
            for r in requirements
        ]

        normalized_corpus = [
            self._normalize_requirement(text)
            for text in corpus
        ]

        vectorizer = TfidfVectorizer(stop_words="english")

        try:
            tfidf_matrix = vectorizer.fit_transform(normalized_corpus)
            sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        except Exception:
            sim_matrix = [
                [0.0] * len(requirements)
                for _ in range(len(requirements))
            ]

        duplicates = []
        n = len(requirements)

        for i in range(n):
            for j in range(i + 1, n):
                score_tfidf = float(sim_matrix[i][j])

                tokens_a = set(normalized_corpus[i].split())
                tokens_b = set(normalized_corpus[j].split())

                jaccard = (
                    len(tokens_a & tokens_b) /
                    len(tokens_a | tokens_b)
                    if (tokens_a | tokens_b)
                    else 0.0
                )

                effective_score = max(score_tfidf, jaccard)

                if effective_score >= threshold:
                    req_a = requirements[i]
                    req_b = requirements[j]

                    duplicates.append({
                        "requirement_id": req_a["id"],
                        "conflict_with_id": req_b["id"],
                        "issue_type": "duplicate",
                        "title": (
                            f"Near-Duplicate Requirement: "
                            f"{req_a['id']} & {req_b['id']}"
                        ),
                        "description": (
                            f"Requirements {req_a['id']} and {req_b['id']} "
                            f"have a semantic overlap of "
                            f"{int(effective_score * 100)}%. "
                            f"Consider merging them."
                        ),
                        "detected_phrase": (
                            f"Similarity: {round(effective_score, 2)}"
                        ),
                        "severity": "low",
                        "confidence": float(effective_score),
                    })

        return duplicates