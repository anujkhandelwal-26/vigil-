"""
pgvector-backed retrieval. Three real jobs (see docs/architecture.md for
the "why pgvector, not decoration" argument):
  1. similar_cases()  -- analyst decision support + RAG grounding context
  2. policy_lookup()  -- RBI/DPDP/KYC passages, grounding the copilot
  3. (router.py uses the same embedding machinery for intent matching)

Entity lookup (by device/IP/bank-account hash) deliberately stays plain
SQL -- exact identifier joins are the right tool for that question, not
a vector search.
"""
from __future__ import annotations

from app.db import get_conn


def upsert_case_embedding(application_id: str, embedding: list[float], embed_model: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO case_embedding (application_id, embedding, embed_model)
            VALUES (%s, %s, %s)
            ON CONFLICT (application_id) DO UPDATE
              SET embedding = EXCLUDED.embedding, embed_model = EXCLUDED.embed_model
            """,
            (application_id, embedding, embed_model),
        )
        conn.commit()


def similar_cases(embedding: list[float], exclude_application_id: str | None = None, k: int = 5) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT ce.application_id, a.external_ref,
                   (ce.embedding <=> %s::vector) AS distance,
                   d.action, d.risk_score, d.reason_codes,
                   af.verdict AS analyst_verdict
            FROM case_embedding ce
            JOIN application a ON a.id = ce.application_id
            LEFT JOIN LATERAL (
                SELECT action, risk_score, reason_codes
                FROM decision WHERE application_id = ce.application_id
                ORDER BY created_at DESC LIMIT 1
            ) d ON true
            LEFT JOIN LATERAL (
                SELECT verdict FROM analyst_feedback
                WHERE application_id = ce.application_id
                ORDER BY created_at DESC LIMIT 1
            ) af ON true
            WHERE (%s::uuid IS NULL OR ce.application_id != %s::uuid)
            ORDER BY ce.embedding <=> %s::vector
            LIMIT %s
            """,
            (embedding, exclude_application_id, exclude_application_id, embedding, k),
        ).fetchall()
        cols = ["application_id", "external_ref", "distance", "action", "risk_score", "reason_codes", "analyst_verdict"]
        return [dict(zip(cols, r)) for r in rows]


def policy_lookup(embedding: list[float], k: int = 3) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT source, content, (embedding <=> %s::vector) AS distance
            FROM policy_chunk
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (embedding, embedding, k),
        ).fetchall()
        return [{"source": r[0], "content": r[1], "distance": float(r[2])} for r in rows]


def entity_lookup(field: str, value: str, exclude_application_id: str | None = None, limit: int = 20) -> list[dict]:
    allowed_fields = {"device_hash", "ip_prefix", "bank_account_hash", "mobile_hash"}
    if field not in allowed_fields:
        raise ValueError(f"field must be one of {allowed_fields}")
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT a.id, a.external_ref, a.submitted_at,
                   d.action, d.risk_score
            FROM application a
            LEFT JOIN LATERAL (
                SELECT action, risk_score FROM decision
                WHERE application_id = a.id ORDER BY created_at DESC LIMIT 1
            ) d ON true
            WHERE a.{field} = %s AND (%s::uuid IS NULL OR a.id != %s::uuid)
            ORDER BY a.submitted_at DESC
            LIMIT %s
            """,
            (value, exclude_application_id, exclude_application_id, limit),
        ).fetchall()
        cols = ["application_id", "external_ref", "submitted_at", "action", "risk_score"]
        return [dict(zip(cols, r)) for r in rows]


def get_application_by_id(application_id: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM application WHERE id = %s", (application_id,))
        row = cur.fetchone()
        if row is None:
            return None
        cols = [d.name for d in cur.description]
        return dict(zip(cols, row))


def get_reason_code_catalogue() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT code, title, category, customer_safe_text FROM reason_code").fetchall()
        return [{"code": r[0], "title": r[1], "category": r[2], "customer_safe_text": r[3]} for r in rows]
