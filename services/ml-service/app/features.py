"""
VIGIL feature engineering — the SINGLE source of truth for both training
(training/train.py, training/retrain.py) and serving (scoring.py).

Importing this same module in both places is the guard against train/serve
skew: if this file changes, both paths change together. There is a test
(tests/test_features.py) that asserts determinism and stable column order.

PROTECTED / EXCLUDED FROM THE MODEL, by design (see docs/model-card.md):
  gender, age            -> fairness-audit only, read from the DB directly
                             for the post-hoc parity report, never passed here
  device_hash, ip_prefix,
  bank_account_hash,
  mobile_hash             -> identifiers, used for velocity/linkage/ring
                             queries and pgvector retrieval, not model inputs
  pincode_prefix           -> geography can proxy for protected class; used
                             only for ip/pincode distance, not as a raw
                             categorical feature
  label_typology            -> would leak the answer; analysis-only column
"""
from __future__ import annotations

import pandas as pd

CATEGORICAL_FEATURES = [
    "employment_type",
    "product",
    "channel",
    "residence_type",
]

NUMERIC_FEATURES = [
    "city_tier",
    "monthly_income_inr",
    "amount_inr",
    "tenure_months",
    "cibil_score",
    "is_new_to_credit",
    "active_loans",
    "enquiries_30d",
    "max_dpd_12m",
    "credit_utilisation_pct",
    "oldest_account_months",
    "pan_format_valid",
    "pan_name_match_score",
    "aadhaar_pan_linked",
    "name_dob_mismatch",
    "digilocker_docs_fetched",
    "device_reuse_count_30d",
    "is_emulator",
    "is_rooted",
    "app_install_age_days",
    "ip_distinct_apps_24h",
    "ip_pincode_distance_km",
    "vpn_or_proxy",
    "form_fill_seconds",
    "typing_speed_cpm",
    "paste_events",
    "field_corrections",
    "session_screens",
    "night_application",
    "time_since_prev_app_hours",
    "penny_drop_name_match",
    "account_age_months",
    "avg_monthly_credit_inr",
    "salary_credit_regularity",
    "bounce_count_6m",
    "account_shared_with_n_applicants",
    "mobile_age_on_network_days",
    "recent_sim_swap_30d",
    "mobile_name_match",
    # derived / engineered
    "amount_to_income_ratio",
    "income_to_bank_credit_ratio",
    "cibil_score_missing",
]

# Column order is part of the contract — LightGBM and the pydantic schema
# both depend on it being stable across calls.
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

BOOL_COLUMNS = [
    "is_new_to_credit", "pan_format_valid", "aadhaar_pan_linked",
    "name_dob_mismatch", "is_emulator", "is_rooted", "vpn_or_proxy",
    "night_application", "recent_sim_swap_30d",
]


def _to_numeric_bool(series: pd.Series) -> pd.Series:
    return series.map({True: 1, False: 0, "True": 1, "False": 0, "true": 1, "false": 0}).fillna(series)


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame with the raw application columns (as produced by the
    generator / stored in `application`), return a DataFrame with exactly
    FEATURE_COLUMNS, in stable order, ready for LightGBM.

    Deterministic: same input -> same output, every time. Unseen categorical
    levels are mapped to the 'category' dtype's NaN, which LightGBM handles
    natively without raising.
    """
    out = pd.DataFrame(index=df.index)

    for col in BOOL_COLUMNS:
        out[col] = _to_numeric_bool(df[col]).astype("float64")

    out["cibil_score_missing"] = df["cibil_score"].isna().astype("float64")
    out["cibil_score"] = pd.to_numeric(df["cibil_score"], errors="coerce").fillna(-1)
    out["credit_utilisation_pct"] = pd.to_numeric(df["credit_utilisation_pct"], errors="coerce").fillna(-1)
    out["oldest_account_months"] = pd.to_numeric(df["oldest_account_months"], errors="coerce").fillna(-1)
    out["penny_drop_name_match"] = pd.to_numeric(df["penny_drop_name_match"], errors="coerce").fillna(-1)
    out["account_age_months"] = pd.to_numeric(df["account_age_months"], errors="coerce").fillna(-1)
    out["avg_monthly_credit_inr"] = pd.to_numeric(df["avg_monthly_credit_inr"], errors="coerce").fillna(0)
    out["salary_credit_regularity"] = pd.to_numeric(df["salary_credit_regularity"], errors="coerce").fillna(-1)
    out["mobile_age_on_network_days"] = pd.to_numeric(df["mobile_age_on_network_days"], errors="coerce").fillna(-1)
    out["mobile_name_match"] = pd.to_numeric(df["mobile_name_match"], errors="coerce").fillna(-1)
    out["typing_speed_cpm"] = pd.to_numeric(df["typing_speed_cpm"], errors="coerce").fillna(0)
    out["ip_pincode_distance_km"] = pd.to_numeric(df["ip_pincode_distance_km"], errors="coerce").fillna(0)
    out["time_since_prev_app_hours"] = pd.to_numeric(df["time_since_prev_app_hours"], errors="coerce").fillna(9999)

    remaining_numeric = [
        "city_tier", "monthly_income_inr", "amount_inr", "tenure_months",
        "active_loans", "enquiries_30d", "max_dpd_12m",
        "digilocker_docs_fetched", "device_reuse_count_30d",
        "app_install_age_days", "ip_distinct_apps_24h",
        "form_fill_seconds", "paste_events", "field_corrections",
        "session_screens", "bounce_count_6m", "account_shared_with_n_applicants",
        "pan_name_match_score",
    ]
    for col in remaining_numeric:
        out[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("float64")

    income = pd.to_numeric(df["monthly_income_inr"], errors="coerce").fillna(0)
    amount = pd.to_numeric(df["amount_inr"], errors="coerce").fillna(0)
    bank_credit = out["avg_monthly_credit_inr"]
    out["amount_to_income_ratio"] = amount / (income + 1.0)
    out["income_to_bank_credit_ratio"] = income / (bank_credit + 1.0)

    for col in CATEGORICAL_FEATURES:
        out[col] = df[col].astype("category")

    return out[FEATURE_COLUMNS]


def build_feature_vector(application: dict) -> pd.DataFrame:
    """Single-application convenience wrapper for the /score endpoint."""
    return build_feature_frame(pd.DataFrame([application]))


# Maps a top SHAP feature name to a whitelisted, regulator-shaped reason
# code (see db/V2__seed_reason_codes.sql). Only features with an obvious,
# defensible plain-language reason are mapped; anything else falls back to
# a generic model-driven code so the guardrail never has to invent one.
FEATURE_TO_REASON_CODE = {
    "device_reuse_count_30d": "DEVICE_REUSE_HIGH",
    "ip_distinct_apps_24h": "IP_MULTI_APPLICANT",
    "enquiries_30d": "BUREAU_ENQUIRY_BURST",
    "is_emulator": "EMULATOR_OR_ROOTED",
    "is_rooted": "EMULATOR_OR_ROOTED",
    "pan_name_match_score": "PAN_NAME_MISMATCH",
    "aadhaar_pan_linked": "AADHAAR_PAN_NOT_LINKED",
    "cibil_score_missing": "THIN_OR_NO_BUREAU_FILE",
    "account_shared_with_n_applicants": "BANK_ACCOUNT_SHARED",
    "penny_drop_name_match": "PENNY_DROP_MISMATCH",
    "income_to_bank_credit_ratio": "INCOME_MISMATCH",
    "recent_sim_swap_30d": "SIM_SWAP_RECENT",
    "mobile_name_match": "MOBILE_NAME_MISMATCH",
    "form_fill_seconds": "BEHAVIOUR_FAST_FORM_FILL",
    "paste_events": "BEHAVIOUR_PASTED_FIELDS",
}
