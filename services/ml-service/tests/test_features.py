"""
Guards against train/serve feature skew (see app/features.py docstring) --
the silent killer: if this file's contract breaks, live scores diverge
from reported training metrics and nobody notices until the demo looks
wrong.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from app.features import build_feature_frame, FEATURE_COLUMNS

RAW_ROW = {
    "age": 29, "gender": "F", "employment_type": "SALARIED", "monthly_income_inr": 62000,
    "city_tier": 2, "pincode_prefix": "560", "residence_type": "RENTED",
    "product": "CONSUMER_DURABLE", "amount_inr": 85000, "tenure_months": 12, "channel": "ANDROID_APP",
    "cibil_score": 712, "is_new_to_credit": False, "active_loans": 2, "enquiries_30d": 6,
    "max_dpd_12m": 0, "credit_utilisation_pct": 46.2, "oldest_account_months": 58,
    "pan_format_valid": True, "pan_name_match_score": 0.94, "aadhaar_pan_linked": True,
    "name_dob_mismatch": False, "digilocker_docs_fetched": 2,
    "device_hash": "x", "device_reuse_count_30d": 1, "is_emulator": False, "is_rooted": False,
    "app_install_age_days": 120, "ip_prefix": "1.2", "ip_distinct_apps_24h": 1,
    "ip_pincode_distance_km": 12.0, "vpn_or_proxy": False,
    "form_fill_seconds": 150.0, "typing_speed_cpm": 180.0, "paste_events": 0,
    "field_corrections": 2, "session_screens": 7, "night_application": False,
    "time_since_prev_app_hours": 900.0,
    "bank_account_hash": "y", "penny_drop_name_match": 0.96, "account_age_months": 40,
    "avg_monthly_credit_inr": 60000, "salary_credit_regularity": 0.9, "bounce_count_6m": 0,
    "account_shared_with_n_applicants": 1,
    "mobile_hash": "z", "mobile_age_on_network_days": 900, "recent_sim_swap_30d": False,
    "mobile_name_match": 0.95,
}


def test_feature_frame_has_exactly_the_contract_columns_in_order():
    df = build_feature_frame(pd.DataFrame([RAW_ROW]))
    assert list(df.columns) == FEATURE_COLUMNS


def test_feature_frame_is_deterministic_across_repeated_calls():
    a = build_feature_frame(pd.DataFrame([RAW_ROW]))
    b = build_feature_frame(pd.DataFrame([RAW_ROW]))
    pd.testing.assert_frame_equal(a, b)


def test_column_order_is_stable_regardless_of_input_key_order():
    shuffled = dict(reversed(list(RAW_ROW.items())))
    a = build_feature_frame(pd.DataFrame([RAW_ROW]))
    b = build_feature_frame(pd.DataFrame([shuffled]))
    assert list(a.columns) == list(b.columns)


def test_missing_cibil_score_is_flagged_not_crashed():
    row = dict(RAW_ROW)
    row["cibil_score"] = None
    row["credit_utilisation_pct"] = None
    row["oldest_account_months"] = None
    df = build_feature_frame(pd.DataFrame([row]))
    assert df["cibil_score_missing"].iloc[0] == 1.0
    assert df["cibil_score"].iloc[0] == -1


def test_unseen_categorical_level_does_not_raise():
    row = dict(RAW_ROW)
    row["employment_type"] = "RETIRED_ASTRONAUT"  # never seen in training
    df = build_feature_frame(pd.DataFrame([row]))
    assert df["employment_type"].iloc[0] == "RETIRED_ASTRONAUT"


def test_protected_attributes_never_enter_the_feature_frame():
    df = build_feature_frame(pd.DataFrame([RAW_ROW]))
    assert "gender" not in df.columns
    assert "age" not in df.columns
    assert "device_hash" not in df.columns
    assert "pincode_prefix" not in df.columns
