"""
Copilot intent router. Embeds the analyst's question with the same
EmbeddingProvider used for retrieval (nomic-embed-text, ~21ms measured on
this hardware) and matches it against a handful of labelled example
questions per intent via cosine similarity. Falls back to keyword matching
if the embedding call fails, so the copilot degrades rather than breaks.

Deliberately not an agent framework: seven fixed intents, a router, and a
context builder per intent is simpler, faster, and far easier to guardrail
than letting the LLM decide which tool to call.
"""
from __future__ import annotations

import math

INTENT_EXAMPLES: dict[str, list[str]] = {
    "EXPLAIN_DECISION": [
        "Why was this flagged?",
        "Why did this application get declined?",
        "What triggered this decision?",
    ],
    "TOP_SIGNALS": [
        "Which signals contributed most to the score?",
        "What were the biggest risk factors here?",
        "Rank the top reasons for this score.",
    ],
    "BEHAVIOUR_DELTA": [
        "What changed from this customer's normal behaviour?",
        "How does this application differ from their past applications?",
        "Is this unusual for this applicant?",
    ],
    "CASE_SUMMARY": [
        "Summarize this case.",
        "Give me an overview of this application.",
        "Brief me on this case.",
    ],
    "ENTITY_LOOKUP": [
        "Show me all cases involving this device.",
        "What other applications used this bank account?",
        "List applications from this IP address.",
    ],
    "SIMILAR_CASES": [
        "Have we seen a case like this before?",
        "Show me similar past cases.",
        "Find comparable applications.",
    ],
    "POLICY_LOOKUP": [
        "What does RBI require here?",
        "What is the DPDP rule on this?",
        "What does policy say about KYC in this situation?",
    ],
}

_KEYWORD_FALLBACK: list[tuple[str, list[str]]] = [
    ("ENTITY_LOOKUP", ["device", "ip address", "bank account", "mobile number", "all cases", "other applications"]),
    ("SIMILAR_CASES", ["similar", "seen before", "comparable", "like this"]),
    ("POLICY_LOOKUP", ["rbi", "dpdp", "policy", "regulation", "kyc rule", "aadhaar act"]),
    ("BEHAVIOUR_DELTA", ["normal behaviour", "normal behavior", "changed", "different from", "unusual for"]),
    ("TOP_SIGNALS", ["top signal", "contributed most", "biggest factor", "rank the reasons"]),
    ("CASE_SUMMARY", ["summarize", "summarise", "overview", "brief me"]),
    ("EXPLAIN_DECISION", ["why was", "why did", "why is this", "flagged", "triggered"]),
]

_example_cache: dict[str, list[tuple[str, list[float]]]] = {}


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _keyword_classify(question: str) -> str:
    q = question.lower()
    for intent, keywords in _KEYWORD_FALLBACK:
        if any(kw in q for kw in keywords):
            return intent
    return "EXPLAIN_DECISION"


def classify_intent(question: str, embed_fn) -> str:
    """embed_fn: callable(text) -> list[float], typically EmbeddingProvider.embed."""
    try:
        if "examples" not in _example_cache:
            pairs = []
            for intent, examples in INTENT_EXAMPLES.items():
                for ex in examples:
                    pairs.append((intent, embed_fn(ex)))
            _example_cache["examples"] = pairs

        q_emb = embed_fn(question)
        best_intent, best_score = "EXPLAIN_DECISION", -1.0
        for intent, ex_emb in _example_cache["examples"]:
            score = _cosine(q_emb, ex_emb)
            if score > best_score:
                best_intent, best_score = intent, score
        return best_intent
    except Exception:
        return _keyword_classify(question)
