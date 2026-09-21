"""
VIGIL synthetic data — typology definitions.

Five typologies are used for TRAINING. A sixth, BOT_RING_NEW_VECTOR, is
generated separately and held out of training entirely — it exists only to
power the "adapts to a new fraud vector" demo sequence (Tier 2).

Each typology plants CORRELATED signals across multiple data blocks. That
correlation is what makes (a) the model learnable from a modest row count
and (b) the SHAP explanations read as a coherent story rather than noise.

Field dictionary and the "why is this a fraud signal" rationale for every
field lives in README.md, generated from FIELD_DICTIONARY below.
"""
import hashlib
import random

CITIES_TIER = {1: ["560", "400", "110", "600", "700"],       # metro pincodes prefixes
               2: ["452", "395", "831", "641", "302"],         # tier-2 city prefixes
               3: ["813", "796", "191", "486", "271"]}         # tier-3 / rural

EMPLOYMENT_TYPES = ["SALARIED", "SELF_EMPLOYED", "GIG_WORKER", "UNEMPLOYED_STUDENT"]
PRODUCTS = ["CONSUMER_DURABLE", "PERSONAL", "TWO_WHEELER", "EDUCATION_TOPUP"]
CHANNELS = ["ANDROID_APP", "IOS_APP", "WEB", "PARTNER_POS"]
RESIDENCE = ["OWNED", "RENTED", "FAMILY"]

TYPOLOGIES = [
    "SYNTHETIC_IDENTITY",
    "MULE_ACCOUNT_RING",
    "DEVICE_FARM",
    "SIM_SWAP_TAKEOVER",
    "INCOME_INFLATION",
]
HELD_OUT_TYPOLOGY = "BOT_RING_NEW_VECTOR"

FIELD_DICTIONARY = [
    # (field, block, type, why_signal)
    ("age", "applicant", "int", "Very young or very old applicants correlate with identity fraud"),
    ("gender", "applicant", "enum", "NEVER a model feature — fairness audit only"),
    ("employment_type", "applicant", "enum", "Unemployed/student applying for large loans is atypical"),
    ("monthly_income_inr", "applicant", "numeric", "Baseline for affordability and income-mismatch checks"),
    ("city_tier", "applicant", "int(1-3)", "Fraud typology mix differs by tier"),
    ("pincode_prefix", "applicant", "text(3)", "DPDP-minimised location; geo-distance velocity signal"),
    ("residence_type", "applicant", "enum", "Weak standalone signal, interacts with income stability"),
    ("product", "loan", "enum", "Consumer durable / POS loans see the most device-farm fraud"),
    ("amount_inr", "loan", "numeric", "Larger tickets raise fraud incentive"),
    ("tenure_months", "loan", "int", "Weak standalone signal"),
    ("channel", "loan", "enum", "App-based channels see more bot/emulator fraud than POS"),
    ("cibil_score", "bureau", "int(300-900) or null", "Null/thin file + high loan amount is a synthetic-identity flag"),
    ("is_new_to_credit", "bureau", "bool", "Combined with device reuse, indicates identity fabrication"),
    ("active_loans", "bureau", "int", "High existing exposure correlates with income inflation fraud"),
    ("enquiries_30d", "bureau", "int", "A burst across lenders is a classic fraud-ring signal"),
    ("max_dpd_12m", "bureau", "int", "Recent severe delinquency"),
    ("credit_utilisation_pct", "bureau", "numeric", "Near-100% utilisation with a new application is a stress signal"),
    ("oldest_account_months", "bureau", "int", "Very young credit history plus high request amount"),
    ("pan_format_valid", "kyc", "bool", "Malformed/forged PAN structure"),
    ("pan_name_match_score", "kyc", "numeric(0-1)", "Low match = possible synthetic identity"),
    ("aadhaar_pan_linked", "kyc", "bool", "Unlinked Aadhaar-PAN is a red flag under RBI KYC norms"),
    ("name_dob_mismatch", "kyc", "bool", "Cross-document inconsistency"),
    ("digilocker_docs_fetched", "kyc", "int", "Zero fetched docs on a large loan is unusual"),
    ("device_hash", "device", "hash", "Salted hash; reused across identities = device farm"),
    ("device_reuse_count_30d", "device", "int", "Core device-farm signal"),
    ("is_emulator", "device", "bool", "Emulated devices are near-exclusively fraud"),
    ("is_rooted", "device", "bool", "Rooted devices bypass integrity checks"),
    ("app_install_age_days", "device", "int", "Fresh install immediately used for a large loan"),
    ("ip_prefix", "device", "text(/16)", "DPDP-minimised; many apps from one prefix = ring"),
    ("ip_distinct_apps_24h", "device", "int", "IP-level velocity"),
    ("ip_pincode_distance_km", "device", "numeric", "Large geo mismatch between IP and stated address"),
    ("vpn_or_proxy", "device", "bool", "Identity concealment signal"),
    ("form_fill_seconds", "behaviour", "numeric", "Sub-normal fill time suggests scripted/bot submission"),
    ("typing_speed_cpm", "behaviour", "numeric", "Implausibly high speed suggests automation"),
    ("paste_events", "behaviour", "int", "Pasted PAN/Aadhaar numbers rather than typed"),
    ("field_corrections", "behaviour", "int", "Zero corrections at high speed is atypical of humans"),
    ("session_screens", "behaviour", "int", "Skipped screens suggest a scripted flow"),
    ("night_application", "behaviour", "bool", "Weak standalone signal, interacts with velocity"),
    ("time_since_prev_app_hours", "behaviour", "numeric", "Rapid repeat applications from the same profile"),
    ("bank_account_hash", "banking", "hash", "Salted hash; shared across applicants = mule ring"),
    ("penny_drop_name_match", "banking", "numeric(0-1)", "Low match = mule/rented account"),
    ("account_age_months", "banking", "int", "Very new accounts used immediately for disbursal"),
    ("avg_monthly_credit_inr", "banking", "numeric", "Compared against declared income for inflation fraud"),
    ("salary_credit_regularity", "banking", "numeric(0-1)", "Irregular credits contradict a 'salaried' declaration"),
    ("bounce_count_6m", "banking", "int", "Repeated bounces signal financial distress / mule turnover"),
    ("account_shared_with_n_applicants", "banking", "int", "Direct ring-membership signal (analysis only, not fed raw to model)"),
    ("mobile_hash", "mobile", "hash", "Salted hash; used for entity-lookup queries"),
    ("mobile_age_on_network_days", "mobile", "int", "New number on network + big loan is atypical"),
    ("recent_sim_swap_30d", "mobile", "bool", "Core SIM-swap-takeover signal"),
    ("mobile_name_match", "mobile", "numeric(0-1)", "Registered owner mismatch"),
]


def salted_hash(value: str, salt: str = "vigil-demo-salt") -> str:
    return "sha256:" + hashlib.sha256(f"{salt}:{value}".encode()).hexdigest()[:16]
