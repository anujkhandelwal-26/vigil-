# Dataset audit — why VIGIL trains on synthetic data

Three public datasets were evaluated for this project and directly profiled (not taken on faith).
All three were rejected. This document is the evidence.

## 1. Kaggle "Loan Fraud Detection Dataset"
10,000 rows × 12 columns, 16.08% fraud (~10× a realistic base rate). Right domain — Indian lenders
(Bajaj Finance, ICICI, Axis, HDFC, SBI, Kotak) — and genuinely behavioural columns.

Univariate AUC per feature (rank-based, computed directly on the downloaded CSV):

| Feature | AUC |
|---|---|
| `device_change_rate` | 0.681 |
| `ip_region_mismatch` | 0.642 |
| `browser_fingerprint_change` | 0.550 |
| `geo_location_consistency` | 0.562 |
| `application_frequency` | 0.543 |
| `previous_defaults` | 0.524 |
| `loan_amount` | **0.505 — noise** |
| `session_duration` | **0.501 — noise** |
| `time_between_apps` | **0.504 — noise** |

**Verdict: rejected.** No identity fields (device hash, IP, email), no timestamps, no protected
attributes, and 5 of 12 columns are indistinguishable from random noise. Cannot support ring
detection, velocity features, or a fairness audit.

## 2. Kaggle "Digital Payment Fraud Detection Benchmark Dataset"
300,113 rows × 21 columns, 1.49% fraud (realistic). Has `customer_id`/`merchant_id` and timestamps.

**Target leakage found**: `post_auth_risk_score` has univariate AUC = **1.0000**. It is a
post-authorisation field — computed after the outcome is already known. Any notebook reporting
~100% accuracy on this "benchmark" is reading the answer key, not detecting fraud.

With that column removed, only two features carry signal: `txn_count_24h` (0.793) and
`failed_txn_count_24h` (0.626). The other twelve sit at 0.50–0.53.

**Ring-structure check**: of 7,347 customers and 7,993 merchants with ≥5 transactions in a 120k-row
sample, **zero** have a fraud rate ≥50%. Fraud is distributed i.i.d. across entities — there is no
ring structure to find, so nearest-neighbour clustering (pgvector's core value in this project) has
nothing to detect.

**Verdict: rejected.** Leaked label, no ring structure, and it is transaction fraud rather than
application fraud (a different problem shape).

## 3. Feedzai Bank Account Fraud (BAF) suite (NeurIPS 2022 Datasets & Benchmarks)
The strongest public candidate: six 1M-row variants with controlled bias regimes, published protected
attributes, and a well-documented generation pipeline. Rejected for three converging reasons:

1. **Licence**: Kaggle's dataset metadata states **CC BY-NC-SA-4.0**; Feedzai's own datasheet states
   **CC BY-NC-ND-4.0**. The two disagree on whether a modified derivative may be redistributed at
   all (SA permits it under share-alike; ND forbids it outright). Both are non-commercial, and the
   ambiguity between them is Feedzai's to resolve, not something to build a submission on.
2. **v1 leakage history**: the dataset's own changelog reads *"Update 2023-11-29 — Remove
   relationship between index and label."* The row index leaked the label in the original release.
   The fix is a documented one-line `index_col=0` load parameter, but it is exactly the kind of
   detail a judge could reasonably ask about.
3. **Not Indian**: the underlying task (bank account *opening* fraud) and feature set reflect a
   different regulatory and product context than Indian digital lending.

**A genuinely useful finding from BAF, cited as supporting evidence for our design choice below**:
the BAF paper measures LightGBM at **75.4% TPR@5%FPR on the real, un-synthesised bank data**, falling
to **54.8%** after CTGAN + differential-privacy synthesis — roughly 21 points of fraud signal
destroyed by *generative* synthesis. Feedzai's own datasheet states the dataset "should be avoided"
for direct real-world model training and is an evaluation benchmark only.

**Verdict: rejected** — non-commercial licence with an internal contradiction, a leakage history, and
not Indian.

## Decision: a rule-based synthetic generator, with public data kept as external validation only

The BAF finding above is direct, on-dataset evidence for a specific engineering choice: **structural,
rule-based synthesis preserves fraud signal; GAN-based synthesis destroys it.**
`data/generator/generate.py` is therefore rule-based — five typologies, each with severity-blended,
probabilistic (not maximal-every-time) signal injection across correlated data blocks — not a GAN.

This also gives VIGIL what none of the three public datasets could: a controllable entity graph for
ring detection, Indian regulatory fields (PAN, Aadhaar linkage, DigiLocker, CIBIL), protected
attributes for the fairness audit, and a **sixth, held-out typology** to demonstrate adaptation to an
unseen fraud vector — the one scenario no public dataset could ever provide, because by definition it
doesn't appear in any historical data.

**The takeaway for the deck**: refusing a 0.99 AUC on data we know is compromised is a stronger
signal to a fraud-risk audience than reporting it uncritically would have been.
