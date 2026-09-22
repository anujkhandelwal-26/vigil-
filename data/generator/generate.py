#!/usr/bin/env python3
"""
VIGIL synthetic Indian digital-lending application generator.

Produces data/generated/applications.csv — 60,000 rows, ~3.5% fraud across
five typologies — plus data/generated/new_vector_injection.csv, twelve
applications of a SIXTH typology (BOT_RING_NEW_VECTOR) that is held out of
training entirely and used only to demo adaptation to an unseen fraud vector.

Deliberately RULE-BASED, not a GAN. The Feedzai Bank Account Fraud paper
measured that CTGAN + differential-privacy synthesis destroys ~21 points of
fraud signal (LightGBM TPR@5%FPR: 75.4% real -> 54.8% synthesised). A
rule-based generator with correlated, typology-specific signal blocks is a
deliberate choice to keep the signal learnable, not a shortcut.

Usage: python generate.py [--n 60000] [--fraud-rate 0.035] [--seed 20260921]
"""
import argparse
import csv
import datetime
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
from typologies import (
    CITIES_TIER, EMPLOYMENT_TYPES, PRODUCTS, CHANNELS, RESIDENCE,
    TYPOLOGIES, HELD_OUT_TYPOLOGY, salted_hash,
)

FIELDNAMES = [
    "external_ref", "submitted_at",
    "age", "gender", "employment_type", "monthly_income_inr", "city_tier",
    "pincode_prefix", "residence_type",
    "product", "amount_inr", "tenure_months", "channel",
    "cibil_score", "is_new_to_credit", "active_loans", "enquiries_30d",
    "max_dpd_12m", "credit_utilisation_pct", "oldest_account_months",
    "pan_format_valid", "pan_name_match_score", "aadhaar_pan_linked",
    "name_dob_mismatch", "digilocker_docs_fetched", "aadhaar_last4",
    "device_hash", "device_reuse_count_30d", "is_emulator", "is_rooted",
    "app_install_age_days", "ip_prefix", "ip_distinct_apps_24h",
    "ip_pincode_distance_km", "vpn_or_proxy",
    "form_fill_seconds", "typing_speed_cpm", "paste_events",
    "field_corrections", "session_screens", "night_application",
    "time_since_prev_app_hours",
    "bank_account_hash", "penny_drop_name_match", "account_age_months",
    "avg_monthly_credit_inr", "salary_credit_regularity", "bounce_count_6m",
    "account_shared_with_n_applicants",
    "mobile_hash", "mobile_age_on_network_days", "recent_sim_swap_30d",
    "mobile_name_match",
    "label_fraud", "label_typology",
]

BASE_TIME = datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=5, minutes=30)))


def rand_timestamp(rng, day_span=112):
    delta = datetime.timedelta(
        days=rng.uniform(0, day_span),
        seconds=rng.randint(0, 86399),
    )
    return (BASE_TIME + delta).isoformat()


def base_legit(rng, idx):
    """A plausible, non-fraudulent Indian digital-lending applicant."""
    tier = rng.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
    age = int(rng.gauss(34, 9))
    age = max(21, min(65, age))
    employment = rng.choices(EMPLOYMENT_TYPES, weights=[0.55, 0.25, 0.15, 0.05])[0]
    income = max(12000, rng.gauss(45000 if employment == "SALARIED" else 30000, 18000))
    cibil_has_file = rng.random() > 0.12
    row = {
        "external_ref": f"APP-2026-{idx:07d}",
        "submitted_at": rand_timestamp(rng),
        "age": age,
        "gender": rng.choices(["M", "F"], weights=[0.63, 0.37])[0],
        "employment_type": employment,
        "monthly_income_inr": round(income, 2),
        "city_tier": tier,
        "pincode_prefix": rng.choice(CITIES_TIER[tier]),
        "residence_type": rng.choices(RESIDENCE, weights=[0.35, 0.45, 0.2])[0],
        "product": rng.choice(PRODUCTS),
        "amount_inr": round(rng.choice([15000, 25000, 40000, 60000, 85000, 120000, 200000])
                             * rng.uniform(0.85, 1.15), 2),
        "tenure_months": rng.choice([3, 6, 9, 12, 18, 24]),
        "channel": rng.choices(CHANNELS, weights=[0.45, 0.25, 0.2, 0.1])[0],
        "cibil_score": int(rng.gauss(715, 70)) if cibil_has_file else None,
        "is_new_to_credit": not cibil_has_file,
        "active_loans": rng.choices([0, 1, 2, 3, 4], weights=[0.3, 0.3, 0.2, 0.15, 0.05])[0],
        "enquiries_30d": rng.choices([0, 1, 2, 3], weights=[0.5, 0.3, 0.15, 0.05])[0],
        "max_dpd_12m": rng.choices([0, 15, 30, 60, 90], weights=[0.8, 0.1, 0.05, 0.03, 0.02])[0],
        "credit_utilisation_pct": round(rng.uniform(5, 55), 2) if cibil_has_file else None,
        "oldest_account_months": int(rng.uniform(12, 180)) if cibil_has_file else None,
        "pan_format_valid": True,
        "pan_name_match_score": round(min(1.0, max(0.4, rng.gauss(0.93, 0.08))), 3),
        "aadhaar_pan_linked": rng.random() > 0.05,
        "name_dob_mismatch": False,
        "digilocker_docs_fetched": rng.choices([0, 1, 2, 3], weights=[0.2, 0.3, 0.3, 0.2])[0],
        "aadhaar_last4": f"{rng.randint(0, 9999):04d}",
        "device_hash": salted_hash(f"device-{idx}-{rng.random()}"),
        "device_reuse_count_30d": rng.choices([0, 1, 2, 3, 4], weights=[0.62, 0.2, 0.1, 0.05, 0.03])[0],
        "is_emulator": rng.random() < 0.015,
        "is_rooted": rng.random() < 0.025,
        "app_install_age_days": int(rng.uniform(5, 900)),
        "ip_prefix": f"{rng.randint(1,223)}.{rng.randint(0,255)}",
        "ip_distinct_apps_24h": rng.choices([1, 2, 3, 4], weights=[0.78, 0.14, 0.05, 0.03])[0],
        "ip_pincode_distance_km": round(rng.uniform(0, 60), 2),
        "vpn_or_proxy": rng.random() < 0.06,
        "form_fill_seconds": round(max(8, rng.gauss(150, 55)), 2),
        "typing_speed_cpm": round(max(50, rng.gauss(190, 70)), 2),
        "paste_events": rng.choices([0, 1, 2, 3], weights=[0.62, 0.22, 0.11, 0.05])[0],
        "field_corrections": rng.choices([0, 1, 2, 3, 4], weights=[0.15, 0.3, 0.3, 0.15, 0.1])[0],
        "session_screens": rng.choices([5, 6, 7, 8], weights=[0.1, 0.3, 0.4, 0.2])[0],
        "night_application": rng.random() < 0.08,
        "time_since_prev_app_hours": round(rng.uniform(72, 2000), 2),
        "bank_account_hash": salted_hash(f"bank-{idx}-{rng.random()}"),
        "penny_drop_name_match": round(max(0.35, rng.gauss(0.92, 0.09)), 3),
        "account_age_months": int(rng.uniform(6, 200)),
        "avg_monthly_credit_inr": round(income * rng.uniform(0.85, 1.1), 2),
        "salary_credit_regularity": round(rng.uniform(0.8, 1.0), 3) if employment == "SALARIED" else round(rng.uniform(0.4, 0.8), 3),
        "bounce_count_6m": rng.choices([0, 1, 2], weights=[0.8, 0.15, 0.05])[0],
        "account_shared_with_n_applicants": rng.choices([1, 2], weights=[0.92, 0.08])[0],
        "mobile_hash": salted_hash(f"mobile-{idx}-{rng.random()}"),
        "mobile_age_on_network_days": int(rng.uniform(180, 3000)),
        "recent_sim_swap_30d": rng.random() < 0.02,
        "mobile_name_match": round(max(0.4, rng.gauss(0.92, 0.09)), 3),
        "label_fraud": False,
        "label_typology": None,
    }
    return row


def apply_synthetic_identity(rng, row):
    sev = rng.uniform(0.3, 1.0)
    row["pan_format_valid"] = rng.random() > (0.5 * sev)
    row["pan_name_match_score"] = round(min(1.0, max(0.05, rng.gauss(0.75 - 0.55 * sev, 0.12))), 3)
    if rng.random() < 0.5 + 0.35 * sev:
        row["aadhaar_pan_linked"] = False
    row["name_dob_mismatch"] = rng.random() < 0.15 + 0.5 * sev
    if rng.random() < 0.4 + 0.5 * sev:
        row["is_new_to_credit"] = True
        row["cibil_score"] = None
        row["credit_utilisation_pct"] = None
        row["oldest_account_months"] = None
    row["digilocker_docs_fetched"] = rng.choices([0, 1, 2], weights=[0.5, 0.3, 0.2])[0]
    row["amount_inr"] = round(row["amount_inr"] * rng.uniform(1.0, 1.0 + 0.6 * sev), 2)
    return row


def apply_mule_account_ring(rng, ring_account_hash, ring_size, row):
    sev = rng.uniform(0.3, 1.0)
    if rng.random() < 0.85:
        row["bank_account_hash"] = ring_account_hash
        row["account_shared_with_n_applicants"] = max(1, int(ring_size * rng.uniform(0.4, 1.0)))
    else:
        row["account_shared_with_n_applicants"] = rng.choices([1, 2], weights=[0.3, 0.7])[0]
    row["penny_drop_name_match"] = round(max(0.05, rng.gauss(0.7 - 0.5 * sev, 0.15)), 3)
    row["account_age_months"] = int(rng.uniform(1, 1 + 10 * (1 - sev)))
    row["bounce_count_6m"] = rng.choices([0, 1, 2, 3], weights=[0.35, 0.3, 0.2, 0.15])[0]
    row["avg_monthly_credit_inr"] = round(row["monthly_income_inr"] * rng.uniform(0.3 + 0.3*(1-sev), 0.9), 2)
    row["salary_credit_regularity"] = round(max(0.05, rng.gauss(0.55 - 0.35 * sev, 0.15)), 3)
    return row


def apply_device_farm(rng, ring_device_hash, ring_size, row):
    sev = rng.uniform(0.3, 1.0)
    if rng.random() < 0.8:
        row["device_hash"] = ring_device_hash
        row["device_reuse_count_30d"] = max(1, int(ring_size * rng.uniform(0.4, 1.0)))
    row["is_emulator"] = rng.random() < 0.15 + 0.5 * sev
    row["is_rooted"] = rng.random() < 0.15 + 0.45 * sev
    row["app_install_age_days"] = int(rng.uniform(0, 1 + 8 * (1 - sev)))
    row["form_fill_seconds"] = round(max(5, rng.gauss(140 - 110 * sev, 30)), 2)
    row["typing_speed_cpm"] = round(max(60, rng.gauss(220 + 500 * sev, 90)), 2)
    row["paste_events"] = rng.choices([0, 1, 2, 3, 4], weights=[0.15, 0.2, 0.25, 0.25, 0.15])[0]
    row["field_corrections"] = rng.choices([0, 1], weights=[0.6 + 0.3*sev, 0.4 - 0.3*sev])[0]
    row["session_screens"] = rng.choices([2, 3, 4, 5], weights=[0.3*sev, 0.3, 0.25, 0.15])[0]
    row["ip_distinct_apps_24h"] = max(1, int(ring_size * rng.uniform(0.3, 0.9))) if rng.random() < 0.7 else rng.choices([1,2],weights=[0.7,0.3])[0]
    row["vpn_or_proxy"] = rng.random() < 0.15 + 0.4 * sev
    return row


def apply_sim_swap_takeover(rng, row):
    sev = rng.uniform(0.3, 1.0)
    row["recent_sim_swap_30d"] = rng.random() < 0.4 + 0.55 * sev
    row["mobile_age_on_network_days"] = int(rng.uniform(0, 3 + 40 * (1 - sev)))
    row["mobile_name_match"] = round(max(0.05, rng.gauss(0.75 - 0.5 * sev, 0.15)), 3)
    row["device_reuse_count_30d"] = rng.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
    row["app_install_age_days"] = int(rng.uniform(0, 2 + 10 * (1 - sev)))
    row["time_since_prev_app_hours"] = round(rng.uniform(0, 6 + 40 * (1 - sev)), 2)
    return row


def apply_income_inflation(rng, row):
    sev = rng.uniform(0.3, 1.0)
    declared = row["monthly_income_inr"] * rng.uniform(1.3, 1.3 + 2.0 * sev)
    row["monthly_income_inr"] = round(declared, 2)
    row["avg_monthly_credit_inr"] = round(declared * rng.uniform(0.15, 0.6), 2)
    row["salary_credit_regularity"] = round(max(0.05, rng.gauss(0.55 - 0.35 * sev, 0.15)), 3)
    row["bounce_count_6m"] = rng.choices([0, 1, 2, 3, 4], weights=[0.15, 0.25, 0.25, 0.2, 0.15])[0]
    row["amount_inr"] = round(row["amount_inr"] * rng.uniform(1.1, 1.1 + 0.9 * sev), 2)
    return row


def apply_bot_ring_new_vector(rng, ring_device_hash, idx, row):
    """
    HELD OUT OF TRAINING. Clean bureau data (so the supervised model has no
    reason to flag it), but a behavioural/device signature that has never
    appeared in training: sub-second-scale form fill, headless fingerprint
    proxy (paste_events maxed + zero corrections + minimal screens), one
    device across many identities, several IPs in one /24 -- a bot ring
    that would only be caught by unsupervised novelty detection + embedding
    similarity clustering, not by the supervised model or a device_hash
    GROUP BY (because in a fuller attack it would also rotate devices).
    """
    row["cibil_score"] = int(rng.gauss(730, 40))
    row["is_new_to_credit"] = False
    row["credit_utilisation_pct"] = round(rng.uniform(10, 30), 2)
    row["oldest_account_months"] = int(rng.uniform(24, 96))
    row["max_dpd_12m"] = 0
    row["pan_format_valid"] = True
    row["pan_name_match_score"] = round(rng.uniform(0.85, 0.98), 3)
    row["aadhaar_pan_linked"] = True
    row["device_hash"] = ring_device_hash
    row["device_reuse_count_30d"] = 12
    row["is_emulator"] = True
    row["is_rooted"] = False
    row["app_install_age_days"] = 0
    row["ip_prefix"] = f"103.{rng.choice([21, 22, 23, 24])}"
    row["ip_distinct_apps_24h"] = 12
    row["vpn_or_proxy"] = True
    row["form_fill_seconds"] = round(rng.uniform(4, 9), 2)
    row["typing_speed_cpm"] = round(rng.uniform(700, 1100), 2)
    row["paste_events"] = 6
    row["field_corrections"] = 0
    row["session_screens"] = 2
    row["night_application"] = True
    row["label_fraud"] = True
    row["label_typology"] = HELD_OUT_TYPOLOGY
    return row


def generate(n, fraud_rate, seed):
    rng = random.Random(seed)
    n_fraud = int(n * fraud_rate)
    fraud_idx = set(rng.sample(range(n), n_fraud))

    per_typology = n_fraud // len(TYPOLOGIES)
    typ_assignment = {}
    idx_list = sorted(fraud_idx)
    for i, idx in enumerate(idx_list):
        typ_assignment[idx] = TYPOLOGIES[min(i // max(per_typology, 1), len(TYPOLOGIES) - 1)]

    device_farm_rings = {}
    mule_rings = {}
    device_farm_indices = [i for i, t in typ_assignment.items() if t == "DEVICE_FARM"]
    mule_indices = [i for i, t in typ_assignment.items() if t == "MULE_ACCOUNT_RING"]

    def assign_rings(indices, min_size=4, max_size=14):
        rings = {}
        i = 0
        ring_id = 0
        while i < len(indices):
            size = rng.randint(min_size, max_size)
            chunk = indices[i:i + size]
            for idx in chunk:
                rings[idx] = ring_id
            ring_id += 1
            i += size
        return rings

    device_farm_ring_assign = assign_rings(device_farm_indices)
    mule_ring_assign = assign_rings(mule_indices)
    device_farm_hashes = {rid: salted_hash(f"devicefarm-ring-{rid}-{seed}") for rid in set(device_farm_ring_assign.values())}
    mule_hashes = {rid: salted_hash(f"mule-ring-{rid}-{seed}") for rid in set(mule_ring_assign.values())}
    device_farm_sizes = {}
    for rid in set(device_farm_ring_assign.values()):
        device_farm_sizes[rid] = sum(1 for v in device_farm_ring_assign.values() if v == rid)
    mule_sizes = {}
    for rid in set(mule_ring_assign.values()):
        mule_sizes[rid] = sum(1 for v in mule_ring_assign.values() if v == rid)

    rows = []
    for idx in range(n):
        row = base_legit(rng, idx)
        if idx in fraud_idx:
            typ = typ_assignment[idx]
            row["label_fraud"] = True
            row["label_typology"] = typ
            if typ == "SYNTHETIC_IDENTITY":
                row = apply_synthetic_identity(rng, row)
            elif typ == "MULE_ACCOUNT_RING":
                rid = mule_ring_assign[idx]
                row = apply_mule_account_ring(rng, mule_hashes[rid], mule_sizes[rid], row)
            elif typ == "DEVICE_FARM":
                rid = device_farm_ring_assign[idx]
                row = apply_device_farm(rng, device_farm_hashes[rid], device_farm_sizes[rid], row)
            elif typ == "SIM_SWAP_TAKEOVER":
                row = apply_sim_swap_takeover(rng, row)
            elif typ == "INCOME_INFLATION":
                row = apply_income_inflation(rng, row)
        rows.append(row)
    return rows


def generate_held_out_ring(seed, n=12):
    rng = random.Random(seed + 999)
    ring_device = salted_hash(f"bot-ring-new-vector-{seed}")
    rows = []
    for i in range(n):
        row = base_legit(rng, 900000 + i)
        row = apply_bot_ring_new_vector(rng, ring_device, i, row)
        rows.append(row)
    return rows


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60000)
    ap.add_argument("--fraud-rate", type=float, default=0.035)
    ap.add_argument("--seed", type=int, default=20260921)
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(__file__), "..", "generated"))
    args = ap.parse_args()

    print(f"generating {args.n} applications, target fraud rate {args.fraud_rate}, seed {args.seed}")
    rows = generate(args.n, args.fraud_rate, args.seed)
    actual_fraud = sum(1 for r in rows if r["label_fraud"])
    print(f"actual fraud rows: {actual_fraud} ({actual_fraud/args.n:.4f})")

    by_typ = {}
    for r in rows:
        if r["label_fraud"]:
            by_typ[r["label_typology"]] = by_typ.get(r["label_typology"], 0) + 1
    print("by typology:", by_typ)

    out_main = os.path.join(args.out_dir, "applications.csv")
    write_csv(out_main, rows)
    print(f"wrote {out_main}")

    held_out_rows = generate_held_out_ring(args.seed)
    out_held = os.path.join(args.out_dir, "new_vector_injection.csv")
    write_csv(out_held, held_out_rows)
    print(f"wrote {out_held} ({len(held_out_rows)} rows, typology={HELD_OUT_TYPOLOGY}, HELD OUT OF TRAINING)")


if __name__ == "__main__":
    main()
