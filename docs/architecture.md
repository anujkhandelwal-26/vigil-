# Architecture

## Services

| Service | Tech | Port | Responsibility |
|---|---|---|---|
| `decision-api` | Spring Boot 4.1.1 / Java 21 | 8081 | API-first front door: JWT authN/authZ, bean validation, server-side velocity feature assembly, deterministic rule engine, ML orchestration with timeout-bounded fallback, persistence, audit log |
| `ml-service` | FastAPI / Python 3.12 | 8001 | Stateless inference sidecar: LightGBM score, SHAP explanation, IsolationForest novelty, embeddings, pgvector retrieval, RAG copilot, guardrails |
| `web` | React 18 + Redux Toolkit + RTK Query | 5174 | Application dashboard (editable scenario submission) + Analyst dashboard (queue, case detail, copilot) |
| `db` | `pgvector/pgvector:pg16` | 5433 | PostgreSQL + pgvector, single database |
| Ollama | host process | 11434 | `qwen2.5:3b-instruct-q4_K_M` (LLM) + `nomic-embed-text` (embeddings) |

Java is the mandated, API-first backend; Python is a stateless inference sidecar Java calls over
HTTP with a short, enforced timeout. This is a deliberate boundary: independently testable,
independently scalable, and it is how this pattern is built in production fraud systems.

## Why the LLM is off the hot path — the single most important decision here

Measured on the development machine: `qwen2.5:3b-instruct-q4_K_M` warm round-trip is **~0.4s**;
`nomic-embed-text` is **~21ms**. A 0.4s call cannot sit inside a "real-time" scoring budget. So:

- **The embedding is cheap enough to be near-synchronous** — it runs in an async task immediately
  after the HTTP response is written (FastAPI `BackgroundTasks`), so it never adds latency to the
  caller but is available within tens of milliseconds for the next similar-case query.
- **The LLM only runs on explicit analyst action** — generating a case narrative or answering a
  copilot question, both cached after the first call (`llm_explanation` table).

This is why the scoring path can credibly claim "real-time" (measured p95 ≈ 99ms end-to-end,
p95 ≈ 42ms for `ml-service` alone) while still offering LLM-generated prose elsewhere in the product.

## Request path — `POST /api/v1/applications`

```
1. JWT verify + @Valid bean validation ................ ~2ms
2. FeatureAssembler: velocity SQL (device/IP/bank/mobile,
   indexed, server-computed — NOT trusted from the client) . ~8ms
3. RuleEngine: ~15 deterministic rules, in-memory,
   can only ESCALATE the action, never downgrade one
   the model already raised ............................ <1ms
4. MlClient -> ml-service /internal/score
   (150ms timeout; falls back to rules-only on failure) .. 30-55ms
     - LightGBM predict ................................. ~1ms
     - IsolationForest predict .......................... ~1ms
     - SHAP TreeExplainer ............................... ~5-15ms
5. Combine rule-engine action and model action by
   severity (APPROVE < STEP_UP < REVIEW < DECLINE) ...... <1ms
6. Persist application + decision ...................... ~5ms
                                          p50 ≈ 60ms, measured p95 ≈ 99ms
```

### Why velocity is server-computed, not trusted from the client
`FeatureAssembler` queries `application` for how many prior rows share this `device_hash`,
`ip_prefix`, or `bank_account_hash` within a rolling window, and takes `max(client-submitted,
server-computed)`. This means: (a) a client cannot understate its own risk by lying about reuse
counts, and (b) a real ring building up across several submissions *during a live demo* is
genuinely detected — not replayed from a canned payload. This was verified directly: 200
sequential requests reusing a small pool of device/bank hashes correctly escalated later requests
to REVIEW/DECLINE as the server-observed reuse count crossed the rule thresholds.

### Graceful degradation
If `ml-service` doesn't respond within its timeout (or errors), `MlClient` catches the failure and
returns `degraded=true` with a rules-only decision (reason code `ML_UNAVAILABLE_RULES_ONLY`) rather
than propagating a 500 to the caller. Covered by `MlClientFallbackTest`.

## Database schema

`CREATE EXTENSION vector;` first. Key tables:
- `application` — six data blocks (applicant, loan, bureau, kyc, device, behaviour, banking,
  mobile), flattened. Protected attributes (`gender`, `age`) are stored but never read by the
  feature-building code that feeds the model.
- `decision` — `risk_score`, `anomaly_score`, `action`, `reason_codes[]`, `shap_top` (JSON), latency.
- `case_embedding` — `embedding vector(768)`, one row per scored application. No ANN index yet:
  exact cosine-distance scan is ~40ms at this scale and always correct; `ivfflat`/`hnsw` would need
  data present before index build and can silently degrade recall if `lists` is mistuned.
- `policy_chunk` — RBI/DPDP/KYC text chunks with embeddings, the copilot's policy-grounding corpus.
- `reason_code` — the LLM output whitelist.
- `analyst_feedback`, `model_registry`, `llm_explanation`, `audit_log`, `consent_record`.

**Hibernate rule enforced throughout the codebase: no `vector` column is ever mapped in JPA.**
`decision-api`'s entities are plain columns only; Python owns every `vector` column via raw
`psycopg` SQL, and Java gets similarity results by calling `ml-service`. This avoids an entire class
of Hibernate custom-type friction.

## The RAG copilot

Seven fixed intents (`EXPLAIN_DECISION`, `TOP_SIGNALS`, `BEHAVIOUR_DELTA`, `CASE_SUMMARY`,
`ENTITY_LOOKUP`, `SIMILAR_CASES`, `POLICY_LOOKUP`), routed by embedding the analyst's question and
matching it against a handful of labelled examples per intent (cosine similarity), with a keyword
fallback if the embedding call fails. Deliberately not an agent framework — seven fixed intents, a
router, and a per-intent context builder is simpler, faster, and far easier to guardrail than
letting the LLM decide which tool to call.

`ENTITY_LOOKUP` ("show me all cases on this device") is answered with **plain SQL**, not a vector
search — exact identifier joins are the right tool for that question, and using pgvector for it
would be worse, not better.

## Docker build notes

All three Dockerfiles were build-tested and run-tested, not just written: `docker build` on each,
then `docker run` against the real Postgres via `host.docker.internal` (decision-api reached
`/actuator/health` 200; ml-service booted clean). One real bug was caught this way:
`python:3.12-slim` omits `libgomp1` (the OpenMP runtime), which LightGBM's native library requires —
without it the container fails at import time with `OSError: libgomp.so.1: cannot open shared object
file`. Fixed by installing `libgomp1` via `apt-get` before the pip install layer in
`services/ml-service/Dockerfile`. `docker compose --profile full config` also validates cleanly.

## Ring detection threshold calibration

`nomic-embed-text` embeddings of the structured behavioural-profile text used for ring detection
turned out to be far more tightly clustered than typical prose embeddings — an initial threshold of
0.15 cosine distance (a reasonable prior for sentence embeddings) grouped **every** application
submitted close together in time into one "ring", including genuinely unrelated clean applicants.

Measured directly against known-similar and known-dissimilar application pairs:

| Pair | Cosine distance |
|---|---|
| Two members of a real ring (shared device hash) | ~0.0002 |
| Two members of a real ring (identifiers rotated, same behaviour) | ~0.0002 (internally), ~0.096 to an unrelated ring |
| A borderline legitimate profile (young, new-to-credit, night application) vs. a real ring | ~0.008 |
| Two genuinely unrelated clean applicants | ~0.15–0.16 |

The threshold was recalibrated to **0.005** — an order of magnitude above true ring cohesion and
comfortably below the nearest borderline case found during calibration. Re-tested against two
synthetic rings (one sharing an identifier, one with every identifier rotated) plus three genuinely
unrelated clean applications: both rings correctly detected, all three noise cases correctly
excluded. See `services/ml-service/app/rings.py` and `tests/test_rings.py`.

**The lesson generalises**: a plausible-looking default for a vector-similarity threshold is not a
substitute for measuring it against your actual embedding model and your actual data. This was
caught during development precisely by testing with deliberately dissimilar applications, not just
the happy path.

## Boot 4 / Jackson 3 notes (for anyone building on this)
This project targets **Spring Boot 4.1.1**, which defaults to **Jackson 3** internally
(`tools.jackson.*`). `decision-api` explicitly pulls in classic Jackson 2
(`com.fasterxml.jackson.core:jackson-databind`) as a compile dependency for its own JSON handling
(`MlRestClientConfig`, `DecisionService`), because the snake_case ↔ camelCase field mapping to
`ml-service`'s pydantic schema is built on the classic `MappingJackson2HttpMessageConverter`. Two
digit-boundary naming gotchas were found and fixed during development: Hibernate's implicit naming
strategy and Jackson's `SNAKE_CASE` strategy both fail to insert an underscore before a digit
(`enquiries30d` instead of `enquiries_30d`), so every entity column name and every field on
`MlScoreRequest` with an embedded digit is **explicitly annotated** rather than left to the default
converter.
