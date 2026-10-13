import re
from typing import List, Dict, Any

class AmbiguityAgent:
    """Agent 8.5: Ambiguity Detection Agent
    Detects fuzzy and decision-relevant ambiguous language (Section 8.5).
    Generates targeted clarification questions with suggested quantifiable bounds.
    """

    AMBIGUOUS_PATTERNS = [
        {
            "term": "fast",
            "pattern": r"\b(fast|quick|rapid|speedy)\b",
            "severity": "medium",
            "question": "What is the maximum acceptable latency or response time (e.g., < 500ms, < 2s) under normal and peak loads?",
            "suggested_options": ["< 200ms API response", "< 1 second page load", "< 3 seconds for heavy reports"]
        },
        {
            "term": "user-friendly",
            "pattern": r"\b(user-friendly|intuitive|easy to use|simple interface|convenient)\b",
            "severity": "low",
            "question": "What specific usability standards, maximum click depths, or accessibility criteria (e.g., WCAG 2.1 AA) must be met?",
            "suggested_options": ["WCAG 2.1 AA compliant", "Tasks completable in <= 3 clicks", "Mobile-first responsive design"]
        },
        {
            "term": "secure",
            "pattern": r"\b(secure|safe|bulletproof security|protected)\b",
            "severity": "high",
            "question": "What encryption standards (e.g., AES-256, TLS 1.3), authentication mechanisms (MFA, OAuth2), and compliance policies are required?",
            "suggested_options": ["TLS 1.3 in transit + AES-256 at rest", "OAuth2 / JWT with RBAC", "SOC2 / GDPR compliance"]
        },
        {
            "term": "efficient",
            "pattern": r"\b(efficient|optimized|minimal overhead)\b",
            "severity": "medium",
            "question": "What specific throughput, CPU/memory limits, or query time thresholds define efficiency?",
            "suggested_options": ["< 50MB RAM per worker", "Support 1000 requests/sec", "Database query execution < 50ms"]
        },
        {
            "term": "appropriate",
            "pattern": r"\b(appropriate|reasonable|adequate|sufficient|suitable)\b",
            "severity": "medium",
            "question": "What concrete rules or quantitative thresholds define 'appropriate' behavior in this context?",
            "suggested_options": ["Configurable by admin in system settings", "Defined by explicit business rules table"]
        },
        {
            "term": "soon",
            "pattern": r"\b(soon|shortly|timely|in real time|as soon as possible|instantly)\b",
            "severity": "medium",
            "question": "What exact maximum delay is permissible (e.g., within 5 seconds, within 1 minute, batch every hour)?",
            "suggested_options": ["Instant (< 2 seconds via WebSocket/SSE)", "Near real-time (< 30 seconds)", "Batched every 5 minutes"]
        },
        {
            "term": "flexible",
            "pattern": r"\b(flexible|modular|customizable|extensible)\b",
            "severity": "low",
            "question": "What specific components or schemas must support user or admin customization without code changes?",
            "suggested_options": ["Customizable fields via JSON schema", "Configurable plugin architecture", "Admin UI role permissions"]
        },
        {
            "term": "large",
            "pattern": r"\b(large|huge|many users|high volume)\b",
            "severity": "high",
            "question": "What is the expected number of concurrent active users, daily transactions, and data storage growth?",
            "suggested_options": ["10,000 daily active users", "500 concurrent sessions", "100 GB database growth/year"]
        }
    ]

    def detect_ambiguities(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        issues = []
        for req in requirements:
            text = f"{req.get('summary', '')} {req.get('description', '')}"
            for item in self.AMBIGUOUS_PATTERNS:
                match = re.search(item["pattern"], text, re.IGNORECASE)
                if match:
                    detected_word = match.group(0)
                    issues.append({
                        "requirement_id": req["id"],
                        "issue_type": "ambiguity",
                        "title": f"Ambiguous specification: '{detected_word}'",
                        "description": f"The term '{detected_word}' is subjective and lacks measurable engineering verification criteria.",
                        "detected_phrase": detected_word,
                        "severity": item["severity"],
                        "confidence": 0.88,
                        "question": item["question"],
                        "suggested_options": item["suggested_options"]
                    })
        return issues
