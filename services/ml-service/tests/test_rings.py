"""
The most novel claim in this repo -- pgvector fraud-ring detection via
behavioural embedding similarity, independent of any shared identifier --
deserves its own test. Plants four near-identical embeddings (a ring) plus
one dissimilar one (noise) and asserts the detector groups exactly the
four, via the behavioural_embedding_only path (no shared device/bank/mobile).
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app import rings
from app.db import get_conn


def _insert_application(app_id: str, unique: str):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO application (
                id, external_ref, age, gender, employment_type, monthly_income_inr,
                city_tier, pincode_prefix, residence_type, product, amount_inr, tenure_months,
                channel, is_new_to_credit, active_loans, enquiries_30d, max_dpd_12m,
                pan_format_valid, pan_name_match_score, aadhaar_pan_linked, name_dob_mismatch,
                digilocker_docs_fetched, device_hash, device_reuse_count_30d, is_emulator,
                is_rooted, app_install_age_days, ip_prefix, ip_distinct_apps_24h, vpn_or_proxy,
                form_fill_seconds, paste_events, field_corrections, session_screens,
                night_application, bank_account_hash, bounce_count_6m,
                account_shared_with_n_applicants, mobile_hash, recent_sim_swap_30d
            ) VALUES (
                %s, %s, 30, 'M', 'GIG_WORKER', 30000, 1, '400', 'RENTED', 'PERSONAL', 40000, 6,
                'ANDROID_APP', true, 0, 0, 0, true, 0.6, false, false, 0,
                %s, 0, true, true, 0, '9.9', 0, true,
                8, 5, 0, 2, true, %s, 2, 1, %s, true
            )
            """,
            (app_id, unique, f"device-{unique}", f"bank-{unique}", f"mobile-{unique}"),
        )
        conn.commit()


def _insert_embedding(app_id: str, vec: list[float]):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO case_embedding (application_id, embedding, embed_model) VALUES (%s, %s, 'test')",
            (app_id, vec),
        )
        conn.commit()


@pytest.fixture
def ring_and_noise():
    ring_ids, noise_id = [], None
    base = [0.1] * 768
    for i in range(4):
        app_id = str(uuid.uuid4())
        unique = f"ringtest-{app_id}"
        _insert_application(app_id, unique)
        # near-identical vectors -> tiny cosine distance
        vec = [v + (0.0001 * i) for v in base]
        _insert_embedding(app_id, vec)
        ring_ids.append(app_id)

    noise_id = str(uuid.uuid4())
    unique = f"ringtest-noise-{noise_id}"
    _insert_application(noise_id, unique)
    noise_vec = [-v for v in base]  # opposite direction -> large cosine distance
    _insert_embedding(noise_id, noise_vec)

    yield ring_ids, noise_id

    with get_conn() as conn:
        all_ids = ring_ids + [noise_id]
        conn.execute("DELETE FROM fraud_ring_member WHERE application_id = ANY(%s::uuid[])", (all_ids,))
        conn.execute("DELETE FROM case_embedding WHERE application_id = ANY(%s::uuid[])", (all_ids,))
        conn.execute("DELETE FROM application WHERE id = ANY(%s::uuid[])", (all_ids,))
        conn.commit()


def test_ring_detector_groups_exactly_the_similar_four(ring_and_noise):
    ring_ids, noise_id = ring_and_noise

    result = rings.detect_for_application(ring_ids[0])

    assert result is not None
    assert result["member_count"] == 4
    assert result["detection_method"] == "behavioural_embedding_only"

    for app_id in ring_ids:
        r = rings.get_ring_for_application(app_id)
        assert r is not None
        assert r["ring_id"] == result["ring_id"]

    noise_ring = rings.get_ring_for_application(noise_id)
    assert noise_ring is None


def test_two_similar_applications_do_not_form_a_ring(ring_and_noise):
    # MIN_RING_SIZE=3: two similar cases alone should not be labelled a ring.
    ring_ids, _ = ring_and_noise
    with get_conn() as conn:
        conn.execute("DELETE FROM case_embedding WHERE application_id = ANY(%s::uuid[])", (ring_ids[2:],))
        conn.commit()
    result = rings.detect_for_application(ring_ids[0])
    assert result is None
