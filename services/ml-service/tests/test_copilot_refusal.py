"""
Proves the copilot never fabricates an answer when it has nothing to
ground one in -- it must refuse (or state the informative "none found"
fact) rather than let the LLM improvise. Runs against the local Postgres
(already running for the dev stack; no Testcontainers -- see
docs/architecture.md "riskiest parts" for the rationale).
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from app.copilot import context as ctx
from app.db import get_conn


@pytest.fixture
def lonely_application():
    """An application sharing no identifiers with anything else in the DB."""
    app_id = str(uuid.uuid4())
    unique = f"test-{app_id}"
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
                %s, %s, 30, 'F', 'SALARIED', 50000, 2, '560', 'RENTED', 'PERSONAL', 50000, 12,
                'WEB', false, 1, 0, 0, true, 0.95, true, false, 2,
                %s, 0, false, false, 100, '9.9', 1, false,
                150, 0, 2, 6, false, %s, 0, 1, %s, false
            )
            """,
            (app_id, unique, f"device-{unique}", f"bank-{unique}", f"mobile-{unique}"),
        )
        conn.commit()
    yield app_id, unique
    with get_conn() as conn:
        conn.execute("DELETE FROM application WHERE id = %s", (app_id,))
        conn.commit()


def test_entity_lookup_with_no_matches_reports_none_found_not_fabricated(lonely_application):
    app_id, unique = lonely_application
    app_row = {"device_hash": f"device-{unique}", "ip_prefix": "9.9",
               "bank_account_hash": f"bank-{unique}", "mobile_hash": f"mobile-{unique}"}
    text, cited_ids = ctx.entity_lookup(app_row, app_id, "Show me all cases involving this device.")
    assert "No other applications" in text
    assert cited_ids == [app_id]


def test_similar_cases_with_no_embedding_does_not_fabricate_neighbours():
    text, cited_ids = ctx.similar_cases("does-not-matter", embedding=None)
    assert "No behavioural embedding on file" in text


def test_behaviour_delta_with_no_prior_applications_says_so(lonely_application):
    app_id, unique = lonely_application
    app_row = {"mobile_hash": f"mobile-{unique}", "device_hash": f"device-{unique}",
               "form_fill_seconds": 150, "amount_inr": 50000}
    text, cited_ids = ctx.behaviour_delta(app_row, app_id)
    assert "No prior applications" in text
