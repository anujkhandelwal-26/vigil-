#!/usr/bin/env python3
"""
DEMO-ONLY FIXTURE BUILDER — not part of the running application.

Reads real rows out of the synthetic training dataset
(data/generated/applications.csv and data/generated/new_vector_injection.csv)
and writes a small, checked-in JSON sample (samples.json) that the Apply
dashboard's scenario picker draws from at runtime, so every "Clean salaried
applicant" / "Device farm" / etc. pick is a genuine, varied record from the
dataset the model was actually trained on, instead of one hardcoded template
repeated verbatim on every click.

This script is run by hand whenever the dataset is regenerated — it is NOT
invoked by `npm run build` or `npm run dev`. Re-run it with:

    python3 web/src/demo-fixtures/build_samples.py

from the repo root, after `data/generator/generate.py` has produced fresh
CSVs.
"""
import csv
import json
import os
import random

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
APPLICATIONS_CSV = os.path.join(ROOT, "data", "generated", "applications.csv")
OUT_PATH = os.path.join(os.path.dirname(__file__), "samples.json")

# new_vector_injection.csv (the held-out BOT_RING_NEW_VECTOR typology) is
# deliberately NOT sampled here: every row in it scores risk_score=1.000
# against the live model (verified directly against ml-service
# /internal/score) -- it's more extreme than the UI scenario needs. That
# scenario stays a single hand-tuned record in scenarios.js instead. See the
# comment there before changing this.

SAMPLES_PER_TYPOLOGY = 40
SEED = 20260921  # same fixed seed the generator uses, for reproducible fixtures

# csv column (snake_case) -> ApplyDashboard field key (camelCase)
FIELD_MAP = [
    ("age", "age", int),
    ("gender", "gender", str),
    ("employment_type", "employmentType", str),
    ("monthly_income_inr", "monthlyIncomeInr", lambda v: round(float(v))),
    ("city_tier", "cityTier", int),
    ("pincode_prefix", "pincodePrefix", str),
    ("residence_type", "residenceType", str),
    ("product", "product", str),
    ("amount_inr", "amountInr", lambda v: round(float(v))),
    ("tenure_months", "tenureMonths", int),
    ("channel", "channel", str),
    ("cibil_score", "cibilScore", lambda v: int(v) if v else None),
    ("is_new_to_credit", "isNewToCredit", lambda v: v == "True"),
    ("active_loans", "activeLoans", int),
    ("enquiries_30d", "enquiries30d", int),
    ("max_dpd_12m", "maxDpd12m", int),
    ("credit_utilisation_pct", "creditUtilisationPct", lambda v: round(float(v), 1) if v else None),
    ("oldest_account_months", "oldestAccountMonths", lambda v: int(v) if v else None),
    ("pan_format_valid", "panFormatValid", lambda v: v == "True"),
    ("pan_name_match_score", "panNameMatchScore", lambda v: round(float(v), 2)),
    ("aadhaar_pan_linked", "aadhaarPanLinked", lambda v: v == "True"),
    ("name_dob_mismatch", "nameDobMismatch", lambda v: v == "True"),
    ("digilocker_docs_fetched", "digilockerDocsFetched", int),
    ("aadhaar_last4", "aadhaarLast4", lambda v: str(v).zfill(4)[-4:]),
    ("device_hash", "deviceHash", str),
    ("device_reuse_count_30d", "deviceReuseCount30d", int),
    ("is_emulator", "isEmulator", lambda v: v == "True"),
    ("is_rooted", "isRooted", lambda v: v == "True"),
    ("app_install_age_days", "appInstallAgeDays", int),
    ("ip_prefix", "ipPrefix", str),
    ("ip_distinct_apps_24h", "ipDistinctApps24h", int),
    ("ip_pincode_distance_km", "ipPincodeDistanceKm", lambda v: round(float(v)) if v else None),
    ("vpn_or_proxy", "vpnOrProxy", lambda v: v == "True"),
    ("form_fill_seconds", "formFillSeconds", lambda v: round(float(v))),
    ("typing_speed_cpm", "typingSpeedCpm", lambda v: round(float(v)) if v else None),
    ("paste_events", "pasteEvents", int),
    ("field_corrections", "fieldCorrections", int),
    ("session_screens", "sessionScreens", int),
    ("night_application", "nightApplication", lambda v: v == "True"),
    ("time_since_prev_app_hours", "timeSincePrevAppHours", lambda v: round(float(v), 1) if v else None),
    ("bank_account_hash", "bankAccountHash", str),
    ("penny_drop_name_match", "pennyDropNameMatch", lambda v: round(float(v), 2) if v else None),
    ("account_age_months", "accountAgeMonths", lambda v: int(v) if v else None),
    ("avg_monthly_credit_inr", "avgMonthlyCreditInr", lambda v: round(float(v)) if v else None),
    ("salary_credit_regularity", "salaryCreditRegularity", lambda v: round(float(v), 2) if v else None),
    ("bounce_count_6m", "bounceCount6m", int),
    ("account_shared_with_n_applicants", "accountSharedWithNApplicants", int),
    ("mobile_hash", "mobileHash", str),
    ("mobile_age_on_network_days", "mobileAgeOnNetworkDays", lambda v: int(v) if v else None),
    ("recent_sim_swap_30d", "recentSimSwap30d", lambda v: v == "True"),
    ("mobile_name_match", "mobileNameMatch", lambda v: round(float(v), 2) if v else None),
]


def convert_row(row):
    out = {}
    for csv_key, js_key, conv in FIELD_MAP:
        raw = row.get(csv_key, "")
        out[js_key] = conv(raw) if raw not in ("", None) else None
    return out


def load_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def main():
    random.seed(SEED)
    rows = load_rows(APPLICATIONS_CSV)
    by_typology = {}
    for row in rows:
        key = row["label_typology"] or "CLEAN"
        by_typology.setdefault(key, []).append(row)

    samples = {}
    for typology, bucket in by_typology.items():
        chosen = random.sample(bucket, min(SAMPLES_PER_TYPOLOGY, len(bucket)))
        samples[typology] = [convert_row(r) for r in chosen]

    with open(OUT_PATH, "w") as f:
        json.dump(samples, f, indent=2, sort_keys=True)

    print(f"wrote {OUT_PATH}")
    for k, v in sorted(samples.items()):
        print(f"  {k}: {len(v)} rows")


if __name__ == "__main__":
    main()
