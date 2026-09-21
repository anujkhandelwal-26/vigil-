-- VIGIL baseline schema.
-- pgvector columns are NEVER mapped in JPA/Hibernate — decision-api treats
-- them as opaque; only ml-service touches `embedding` columns, via raw SQL.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------
-- Users & auth
-- ---------------------------------------------------------------------
CREATE TABLE app_user (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name  TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('ANALYST', 'ADMIN')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Applications — one row per submitted loan application.
-- Six data blocks: applicant, loan, bureau, kyc, device, behaviour,
-- banking, mobile (see README "Training record" for the field dictionary).
-- ---------------------------------------------------------------------
CREATE TABLE application (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_ref          TEXT NOT NULL UNIQUE,
    submitted_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- applicant block
    age                   INT NOT NULL,
    gender                TEXT NOT NULL,                 -- fairness-audit only; NEVER a model feature
    employment_type       TEXT NOT NULL,
    monthly_income_inr    NUMERIC(12,2) NOT NULL,
    city_tier             INT NOT NULL,
    pincode_prefix        TEXT NOT NULL,                  -- DPDP data minimisation: 3 digits only
    residence_type        TEXT NOT NULL,

    -- loan block
    product               TEXT NOT NULL,
    amount_inr            NUMERIC(12,2) NOT NULL,
    tenure_months         INT NOT NULL,
    channel               TEXT NOT NULL,

    -- bureau block
    cibil_score           INT,                            -- NULL / -1 style handling: NULL = no file
    is_new_to_credit      BOOLEAN NOT NULL,
    active_loans          INT NOT NULL,
    enquiries_30d         INT NOT NULL,
    max_dpd_12m           INT NOT NULL,
    credit_utilisation_pct NUMERIC(5,2),
    oldest_account_months INT,

    -- kyc block
    pan_format_valid      BOOLEAN NOT NULL,
    pan_name_match_score  NUMERIC(4,3) NOT NULL,
    aadhaar_pan_linked    BOOLEAN NOT NULL,
    name_dob_mismatch     BOOLEAN NOT NULL,
    digilocker_docs_fetched INT NOT NULL,
    aadhaar_last4         TEXT,                           -- Aadhaar Act s.29: never store the full number

    -- device block (hashed identifiers — salted SHA-256, never raw)
    device_hash           TEXT NOT NULL,
    device_reuse_count_30d INT NOT NULL,
    is_emulator           BOOLEAN NOT NULL,
    is_rooted             BOOLEAN NOT NULL,
    app_install_age_days  INT NOT NULL,
    ip_prefix             TEXT NOT NULL,                  -- DPDP data minimisation: /16 only
    ip_distinct_apps_24h  INT NOT NULL,
    ip_pincode_distance_km NUMERIC(8,2),
    vpn_or_proxy          BOOLEAN NOT NULL,

    -- behaviour block
    form_fill_seconds     NUMERIC(8,2) NOT NULL,
    typing_speed_cpm      NUMERIC(8,2),
    paste_events          INT NOT NULL,
    field_corrections     INT NOT NULL,
    session_screens       INT NOT NULL,
    night_application     BOOLEAN NOT NULL,
    time_since_prev_app_hours NUMERIC(8,2),

    -- banking block
    bank_account_hash     TEXT NOT NULL,
    penny_drop_name_match NUMERIC(4,3),
    account_age_months    INT,
    avg_monthly_credit_inr NUMERIC(12,2),
    salary_credit_regularity NUMERIC(4,3),
    bounce_count_6m       INT NOT NULL,
    account_shared_with_n_applicants INT NOT NULL,

    -- mobile block
    mobile_hash            TEXT NOT NULL,
    mobile_age_on_network_days INT,
    recent_sim_swap_30d    BOOLEAN NOT NULL,
    mobile_name_match      NUMERIC(4,3),

    -- labels (populated by the synthetic generator; analyst_feedback overrides at inference time)
    label_fraud           BOOLEAN,
    label_typology        TEXT,                           -- analysis only, never surfaced to the model

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_application_device_hash  ON application (device_hash);
CREATE INDEX idx_application_ip_prefix    ON application (ip_prefix);
CREATE INDEX idx_application_bank_account ON application (bank_account_hash);
CREATE INDEX idx_application_mobile_hash  ON application (mobile_hash);
CREATE INDEX idx_application_submitted_at ON application (submitted_at DESC);

-- ---------------------------------------------------------------------
-- Decisions
-- ---------------------------------------------------------------------
CREATE TABLE decision (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID NOT NULL REFERENCES application(id),
    model_version   TEXT NOT NULL,
    risk_score      NUMERIC(6,5) NOT NULL,
    anomaly_score   NUMERIC(6,5),
    rule_score      NUMERIC(6,5),
    action          TEXT NOT NULL CHECK (action IN ('APPROVE', 'STEP_UP', 'REVIEW', 'DECLINE')),
    reason_codes    TEXT[] NOT NULL DEFAULT '{}',
    shap_top        JSONB,
    latency_ms      INT NOT NULL,
    degraded        BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_decision_application_id ON decision (application_id);
CREATE INDEX idx_decision_created_at     ON decision (created_at DESC);
CREATE INDEX idx_decision_action         ON decision (action);

-- ---------------------------------------------------------------------
-- pgvector job 1: similar-case retrieval (also the RAG grounding context)
-- ---------------------------------------------------------------------
CREATE TABLE case_embedding (
    application_id UUID PRIMARY KEY REFERENCES application(id),
    embedding      vector(768) NOT NULL,
    embed_model    TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- No ANN index yet: exact scan is ~40ms at 60k rows and always correct.
-- ivfflat/hnsw needs data present before build; add only if there's time (Tier 3).

-- ---------------------------------------------------------------------
-- pgvector job 2: fraud rings
-- ---------------------------------------------------------------------
CREATE TABLE fraud_ring (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label              TEXT,
    detected_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    member_count       INT NOT NULL,
    shared_attributes  JSONB,
    centroid           vector(768),
    total_exposure_inr NUMERIC(14,2),
    detection_method   TEXT NOT NULL
);

CREATE TABLE fraud_ring_member (
    ring_id             UUID NOT NULL REFERENCES fraud_ring(id),
    application_id      UUID NOT NULL REFERENCES application(id),
    distance_to_centroid NUMERIC(8,6),
    PRIMARY KEY (ring_id, application_id)
);

-- ---------------------------------------------------------------------
-- pgvector job 3: policy retrieval (RBI / DPDP / KYC chunks for the copilot)
-- ---------------------------------------------------------------------
CREATE TABLE policy_chunk (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source     TEXT NOT NULL,
    content    TEXT NOT NULL,
    embedding  vector(768),
    embed_model TEXT
);

-- ---------------------------------------------------------------------
-- Reason codes — the LLM whitelist
-- ---------------------------------------------------------------------
CREATE TABLE reason_code (
    code              TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    category          TEXT NOT NULL,
    customer_safe_text TEXT NOT NULL,
    embedding         vector(768)
);

-- ---------------------------------------------------------------------
-- Analyst feedback — the self-learning fuel
-- ---------------------------------------------------------------------
CREATE TABLE analyst_feedback (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id    UUID NOT NULL REFERENCES application(id),
    analyst_id        UUID REFERENCES app_user(id),
    verdict           TEXT NOT NULL CHECK (verdict IN ('FRAUD', 'LEGIT')),
    original_action   TEXT NOT NULL CHECK (original_action IN ('APPROVE', 'STEP_UP', 'REVIEW', 'DECLINE')),
    original_score    NUMERIC(6,5) NOT NULL,
    was_false_positive BOOLEAN NOT NULL,
    note              TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- Model registry
-- ---------------------------------------------------------------------
CREATE TABLE model_registry (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version                TEXT NOT NULL UNIQUE,
    algorithm              TEXT NOT NULL,
    trained_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    training_rows          INT,
    feedback_rows_used     INT DEFAULT 0,
    pr_auc                 NUMERIC(6,5),
    recall_at_1pct_fpr     NUMERIC(6,5),
    fp_rate                NUMERIC(6,5),
    threshold_low          NUMERIC(6,5),
    threshold_high         NUMERIC(6,5),
    threshold_decline      NUMERIC(6,5),
    feature_importance     JSONB,
    active                 BOOLEAN NOT NULL DEFAULT false,
    promoted_reason        TEXT
);

-- ---------------------------------------------------------------------
-- Drift monitoring (Tier 3)
-- ---------------------------------------------------------------------
CREATE TABLE drift_metric (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_name  TEXT NOT NULL,
    window_start  TIMESTAMPTZ NOT NULL,
    window_end    TIMESTAMPTZ NOT NULL,
    psi           NUMERIC(8,5),
    baseline_mean NUMERIC,
    current_mean  NUMERIC,
    breached      BOOLEAN NOT NULL DEFAULT false
);

-- ---------------------------------------------------------------------
-- LLM explanation cache
-- ---------------------------------------------------------------------
CREATE TABLE llm_explanation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      UUID NOT NULL REFERENCES application(id),
    template_version    TEXT NOT NULL,
    provider            TEXT NOT NULL,
    model               TEXT NOT NULL,
    narrative           TEXT NOT NULL,
    cited_reason_codes  TEXT[],
    grounded            BOOLEAN NOT NULL,
    guardrail_violations TEXT[],
    latency_ms          INT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_llm_explanation_app ON llm_explanation (application_id);

-- ---------------------------------------------------------------------
-- Consent (DPDP 2023) & audit
-- ---------------------------------------------------------------------
CREATE TABLE consent_record (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES application(id),
    purpose        TEXT NOT NULL,
    granted_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    withdrawn_at   TIMESTAMPTZ
);

CREATE TABLE audit_log (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor      TEXT NOT NULL,
    action     TEXT NOT NULL,
    entity     TEXT NOT NULL,
    entity_id  TEXT,
    payload    JSONB,
    at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
