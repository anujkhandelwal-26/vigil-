"""
Per-intent context assembly for the copilot. Every function returns
(context_text, cited_ids) -- context_text is what goes verbatim into the
RETRIEVED CONTEXT slot of the prompt template, and every number in it must
be something the guardrail can verify the narrative against.
"""
from __future__ import annotations

from app import retrieval
from app.db import get_conn

_ENTITY_FIELD_KEYWORDS = [
    ("device_hash", ["device"]),
    ("ip_prefix", ["ip address", " ip ", "network address"]),
    ("bank_account_hash", ["bank account", "account"]),
    ("mobile_hash", ["mobile number", "phone number", "mobile"]),
]

# Context builders sometimes retrieve a definitive *absence* of data (no
# priors, no similar cases, no ring, ...). That sentence is already the
# correct, complete answer -- routing it through the LLM for paraphrase is
# where a small local model's refusal reflex tends to fire, discarding a
# real, grounded answer for the generic "I don't have data" line instead.
# Any context_text starting with one of these is passed straight through.
TERMINAL_FINDING_PREFIXES = (
    "No decision found on file",
    "No SHAP contribution data on file",
    "No prior applications on file",
    "No other applications on file share",
    "No behavioural embedding on file",
    "No similar past cases found",
    "No matching policy passages found",
)


def is_terminal_finding(context_text: str) -> bool:
    return context_text.startswith(TERMINAL_FINDING_PREFIXES)


def _get_latest_decision(application_id: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute(
            """SELECT model_version, risk_score, anomaly_score, action, reason_codes,
                      shap_top, latency_ms, created_at
               FROM decision WHERE application_id = %s
               ORDER BY created_at DESC LIMIT 1""",
            (application_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d.name for d in cur.description]
        return dict(zip(cols, row))


def _reason_titles() -> dict[str, str]:
    return {rc["code"]: rc["title"] for rc in retrieval.get_reason_code_catalogue()}


def explain_decision(application: dict, application_id: str) -> tuple[str, list[str]]:
    d = _get_latest_decision(application_id)
    if d is None:
        return "No decision found on file for this application.", []
    titles = _reason_titles()
    reasons = ", ".join(f"{c} ({titles.get(c, c)})" for c in (d["reason_codes"] or []))
    text = (
        f"Application {application['external_ref']}: action={d['action']}, "
        f"risk_score={d['risk_score']}, model_version={d['model_version']}, "
        f"latency_ms={d['latency_ms']}. Reason codes: {reasons or 'none'}."
    )
    return text, [application_id]


def top_signals(application: dict, application_id: str) -> tuple[str, list[str]]:
    d = _get_latest_decision(application_id)
    if d is None or not d.get("shap_top"):
        return "No SHAP contribution data on file for this application.", []
    lines = []
    for s in d["shap_top"]:
        lines.append(f"{s['feature']}={s['value']} contribution={round(s['contribution'], 4)} ({s['direction']})")
    return "Top contributing signals, ranked: " + "; ".join(lines) + ".", [application_id]


def behaviour_delta(application: dict, application_id: str) -> tuple[str, list[str]]:
    with get_conn() as conn:
        cur = conn.execute(
            """SELECT external_ref, form_fill_seconds, device_hash, amount_inr, submitted_at
               FROM application
               WHERE mobile_hash = %s AND id != %s
               ORDER BY submitted_at DESC LIMIT 5""",
            (application["mobile_hash"], application_id),
        )
        cols = [d.name for d in cur.description]
        priors = [dict(zip(cols, r)) for r in cur.fetchall()]
    if not priors:
        return "No prior applications on file for this applicant to compare against.", [application_id]
    avg_fill = sum(p["form_fill_seconds"] for p in priors) / len(priors)
    device_changed = application["device_hash"] not in {p["device_hash"] for p in priors}
    text = (
        f"This applicant has {len(priors)} prior application(s) on file. "
        f"Average prior form-fill time was {round(avg_fill, 1)} seconds vs "
        f"{application['form_fill_seconds']} seconds this time. "
        f"Device changed since the last application: {device_changed}."
    )
    return text, [application_id] + [p["external_ref"] for p in priors]


def case_summary(application: dict, application_id: str) -> tuple[str, list[str]]:
    d = _get_latest_decision(application_id)
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT verdict, note FROM analyst_feedback WHERE application_id = %s ORDER BY created_at DESC LIMIT 1",
            (application_id,),
        )
        fb = cur.fetchone()
    parts = [
        f"Application {application['external_ref']} for INR {application['amount_inr']} "
        f"({application['product']}, {application['tenure_months']} months), "
        f"submitted via {application['channel']}."
    ]
    if d:
        parts.append(f"Decision: {d['action']} at risk_score={d['risk_score']}.")
    if fb:
        parts.append(f"Analyst verdict on file: {fb[0]}.")
    return " ".join(parts), [application_id]


def entity_lookup(application: dict, application_id: str, question: str) -> tuple[str, list[str]]:
    q = question.lower()
    field = "device_hash"
    for f, keywords in _ENTITY_FIELD_KEYWORDS:
        if any(kw in q for kw in keywords):
            field = f
            break
    value = application[field]
    rows = retrieval.entity_lookup(field, value, exclude_application_id=application_id)
    if not rows:
        return f"No other applications on file share this {field.replace('_', ' ')}.", [application_id]
    lines = [f"{r['external_ref']} (action={r['action']}, risk_score={r['risk_score']})" for r in rows]
    text = f"{len(rows)} other application(s) on file share this {field.replace('_', ' ')}: " + "; ".join(lines) + "."
    return text, [application_id] + [r["external_ref"] for r in rows]


def similar_cases(application_id: str, embedding: list[float] | None) -> tuple[str, list[str]]:
    if embedding is None:
        return "No behavioural embedding on file for this application yet.", [application_id]
    rows = retrieval.similar_cases(embedding, exclude_application_id=application_id, k=5)
    if not rows:
        return "No similar past cases found in the case index.", [application_id]
    lines = [
        f"{r['external_ref']} (distance={round(r['distance'], 3)}, action={r['action']}, "
        f"analyst_verdict={r['analyst_verdict'] or 'none'})"
        for r in rows
    ]
    return "Similar past cases by behavioural embedding: " + "; ".join(lines) + ".", [application_id] + [r["external_ref"] for r in rows]


def policy_lookup(application_id: str, embedding: list[float]) -> tuple[str, list[str]]:
    rows = retrieval.policy_lookup(embedding, k=3)
    if not rows:
        return "No matching policy passages found.", []
    lines = [f"[{r['source']}] {r['content']}" for r in rows]
    return " ".join(lines), [r["source"] for r in rows]
