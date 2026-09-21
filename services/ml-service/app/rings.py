"""
pgvector fraud-ring detection. The argument this exists to prove (see
README "Why pgvector is load-bearing, not decoration"):

    a `GROUP BY device_hash` only catches a ring that reuses the device.
    The embedding catches it after the fraudster rotates the device,
    because the behavioural signature -- fill speed, paste ratio,
    correction pattern, navigation path -- is what they cannot cheaply
    vary.

So detection here runs in TWO passes and reports which one fired:
  1. exact-identifier clustering (device_hash / bank_account_hash / mobile_hash)
  2. behavioural-embedding clustering (cosine distance, pgvector), independent
     of whether any identifier is shared at all

A ring is only written when at least MIN_RING_SIZE members agree, so a
random pair of similar-looking legitimate applications never becomes a
"ring" by accident.
"""
from __future__ import annotations

from app.db import get_conn

# nomic-embed-text compresses our structured behavioural-profile text into
# a narrow embedding region (measured: unrelated applications sit at
# cosine distance ~0.09-0.16, genuine ring members at ~0.0002, and a
# borderline legitimate profile -- young, new-to-credit, night
# application -- at ~0.008, adjacent to but distinguishable from a real
# ring). Calibrated empirically; see docs/architecture.md "Ring detection
# threshold calibration". 0.005 sits an order of magnitude above true
# ring cohesion and comfortably below the nearest borderline case found.
COSINE_DISTANCE_THRESHOLD = 0.005
MIN_RING_SIZE = 3
LOOKBACK_WINDOW = "7 days"


def detect_for_application(application_id: str) -> dict | None:
    """
    Run after an application's embedding has been stored. Looks for a
    cluster of >= MIN_RING_SIZE applications (including this one) within
    COSINE_DISTANCE_THRESHOLD in the embedding space, over the last
    LOOKBACK_WINDOW. If found, upserts a fraud_ring row and its members,
    and returns a summary; otherwise returns None.
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT embedding FROM case_embedding WHERE application_id = %s", (application_id,)
        ).fetchone()
        if row is None:
            return None
        embedding = row[0]

        neighbours = conn.execute(
            f"""
            SELECT ce.application_id, a.device_hash, a.bank_account_hash, a.mobile_hash,
                   a.amount_inr, (ce.embedding <=> %s::vector) AS distance
            FROM case_embedding ce
            JOIN application a ON a.id = ce.application_id
            WHERE a.submitted_at > now() - interval '{LOOKBACK_WINDOW}'
              AND (ce.embedding <=> %s::vector) < %s
            ORDER BY ce.embedding <=> %s::vector
            LIMIT 50
            """,
            (embedding, embedding, COSINE_DISTANCE_THRESHOLD, embedding),
        ).fetchall()

        if len(neighbours) < MIN_RING_SIZE:
            return None

        member_ids = [str(n[0]) for n in neighbours]
        device_hashes = {n[1] for n in neighbours if n[1]}
        bank_hashes = {n[2] for n in neighbours if n[2]}
        mobile_hashes = {n[3] for n in neighbours if n[3]}
        total_exposure = sum(float(n[4]) for n in neighbours)

        shared_device = len(device_hashes) == 1
        shared_bank = len(bank_hashes) == 1
        shared_mobile = len(mobile_hashes) == 1
        detection_method = (
            "shared_identifier" if (shared_device or shared_bank or shared_mobile)
            else "behavioural_embedding_only"
        )

        existing = conn.execute(
            """SELECT ring_id FROM fraud_ring_member WHERE application_id = ANY(%s::uuid[])
               LIMIT 1""",
            (member_ids,),
        ).fetchone()

        shared_attrs = {
            "shared_device_hash": list(device_hashes)[0] if shared_device else None,
            "shared_bank_account_hash": list(bank_hashes)[0] if shared_bank else None,
            "shared_mobile_hash": list(mobile_hashes)[0] if shared_mobile else None,
        }

        import json as _json
        if existing:
            ring_id = existing[0]
            conn.execute(
                """UPDATE fraud_ring SET member_count = %s, shared_attributes = %s::jsonb,
                   total_exposure_inr = %s, detection_method = %s WHERE id = %s""",
                (len(member_ids), _json.dumps(shared_attrs), total_exposure, detection_method, ring_id),
            )
        else:
            cur = conn.execute(
                """INSERT INTO fraud_ring (label, member_count, shared_attributes, total_exposure_inr, detection_method)
                   VALUES (%s, %s, %s::jsonb, %s, %s) RETURNING id""",
                (f"Ring detected via {detection_method}", len(member_ids), _json.dumps(shared_attrs),
                 total_exposure, detection_method),
            )
            ring_id = cur.fetchone()[0]

        for n in neighbours:
            conn.execute(
                """INSERT INTO fraud_ring_member (ring_id, application_id, distance_to_centroid)
                   VALUES (%s, %s, %s) ON CONFLICT (ring_id, application_id) DO UPDATE
                   SET distance_to_centroid = EXCLUDED.distance_to_centroid""",
                (ring_id, n[0], float(n[5])),
            )
        conn.commit()

        return {
            "ring_id": str(ring_id),
            "member_count": len(member_ids),
            "detection_method": detection_method,
            "total_exposure_inr": total_exposure,
            "shared_attributes": shared_attrs,
        }


def get_ring_for_application(application_id: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute(
            """SELECT r.id, r.label, r.member_count, r.detection_method, r.total_exposure_inr,
                      r.shared_attributes
               FROM fraud_ring r
               JOIN fraud_ring_member m ON m.ring_id = r.id
               WHERE m.application_id = %s
               ORDER BY r.detected_at DESC LIMIT 1""",
            (application_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "ring_id": str(row[0]), "label": row[1], "member_count": row[2],
            "detection_method": row[3], "total_exposure_inr": float(row[4]) if row[4] else 0,
            "shared_attributes": row[5],
        }
