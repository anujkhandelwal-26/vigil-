# Demo script — recorded walkthrough

Target length: 5–7 minutes. Rehearse from a cold `scripts/seed_demo.sh` at least once before recording.
Pre-warm Ollama (`curl -s -X POST http://localhost:11434/api/generate -d '{"model":"qwen2.5:3b-instruct-q4_K_M","prompt":"hi","stream":false}'`)
right before hitting record so the first narrative/copilot call isn't a cold-start outlier on camera.

---

### 0. Cold open (30s)
**Say:** "Synchrony's problem statement asks for a real-time fraud platform that's self-learning,
reduces false positives, and adapts to fraud patterns it's never seen. Rule-based systems can't do
the third one by definition. This is VIGIL — here's how it does all three, live."

Show the architecture diagram from the README (or a slide) for 5 seconds, then cut to the browser.

---

### 1. Real-time scoring — clean applicant (45s)
- Log in as `analyst`.
- On the **Application** tab, scenario dropdown → **Clean salaried applicant** (already default).
- **Say:** "This is a real loan application form, pre-filled with editable mock data — a tester can
  change any of the ~45 fields across six data blocks: applicant, loan, bureau, KYC, device,
  behaviour, banking, mobile."
- Click **Submit application**.
- **Point at the result:** action badge (APPROVE), risk score, and **the latency number** —
  "54 milliseconds, end to end, through Spring Boot and the Python scoring service. The LLM is not
  in this path at all — that's a deliberate architecture decision, not an accident."

---

### 2. A known fraud typology — Device farm (45s)
- Scenario dropdown → **Device farm (bot ring)**.
- **Say:** "Same form, different applicant — but this one's device has been used eleven times in the
  last thirty days, it's an emulator, and the form was filled in nine seconds."
- Submit. **Point at:** DECLINE badge, reason code chips, SHAP bar chart — "these are the actual
  feature contributions from the trained model, not a canned explanation."

---

### 3. Step-up instead of a hard decline (30s)
- Scenario dropdown → **Velocity burst (rapid re-apply)** (or any borderline scenario that lands
  STEP_UP — verify during rehearsal which scenario currently lands there, since thresholds move on
  retrain).
- **Say:** "A borderline case doesn't get rejected — it gets routed to step-up verification. This is
  the Indian ladder: mobile OTP, Aadhaar offline e-KYC, DigiLocker, penny-drop, video KYC. That's the
  false-positive story: we added friction, not rejection, for exactly this kind of case."

---

### 4. THE moment — a fraud vector the model has never seen (90s)
This is the whole pitch. Slow down here.

- Scenario dropdown → **⚠ New bot ring (unseen by training)**.
- **Say, before clicking submit:** "This typology was never in the training data. Watch the risk
  score."
- Submit.
- **Point at the two numbers:** "Risk score: 0.000. The supervised model — the one that just caught
  the device farm — completely misses this. **But look at the anomaly score: 0.949.**" Point at the
  red **NOVEL PATTERN DETECTED** banner.
- **Say:** "This is a second, independent channel — an IsolationForest fit only on behavioural
  features, deliberately *not* blended into the risk score, because blending would corrupt the
  probability the four-way thresholds depend on. It doesn't know what fraud looks like. It knows what
  *normal* looks like, and this isn't it."

---

### 5. One human decision becomes a learned pattern (90s)
- Switch to the **Analyst** tab.
- Open the case just submitted (top of the queue).
- **Point at:** the SHAP waterfall, the reason codes, **click "Generate narrative"** — wait for the
  `grounded ✓` badge. "The LLM only writes prose here — it never decided anything. Every reason code
  it cites is checked against a whitelist before an analyst ever sees it."
- **Type a copilot question:** "What changed from this customer's normal behaviour?" or click the
  suggested chip. Read the grounded answer.
- **Click Confirm Fraud** with a short note.
- **Say:** "That verdict just became a labelled training example."

---

### 6. Retrain, and recapture (60s)
- Log out, log back in as `admin` (or switch role if you built a quick-switch — otherwise re-login).
- Scroll to **Model registry** → click **Retrain from feedback**.
- **Say while it runs (~3–4 seconds):** "It's rebuilding from the original dataset plus every
  analyst-confirmed case, at higher sample weight. It only promotes the new model if its held-out
  PR-AUC is at least as good as the one it's replacing — self-learning with a gate, not blind
  automation."
- **Point at:** the new version row, `promoted: true`, the reason string.
- Go back to **Application**, resubmit the **exact same bot-ring scenario**.
- **Point at:** the risk score now — measured during development: **0.000 → 0.714**, action moves to
  STEP_UP/REVIEW. "One human decision, and the model adapted. That's the loop."

---

### 7. The ring, the guardrail refusal, and the close (60s)
- **If time allows:** show a ring chip on a case that shares a device hash with others ("Ring #N —
  detected via shared_identifier" or "behavioural_embedding_only" if you demo'd the rotated-identifier
  version during rehearsal).
- **Guardrail proof:** ask the copilot something it has no data for (e.g. "What's this applicant's
  favourite colour?") — show the refusal text, not a fabricated answer.
- **Close:** cut to the architecture diagram / AWS target slide. **Say:** "Real-time scoring in
  milliseconds, an LLM that only writes prose and is checked before anyone sees it, self-learning
  with a promotion gate, and a second channel that catches what the first one can't. Built for the
  Indian market — RBI Digital Lending Directions, DPDP, Aadhaar, CIBIL — and designed so 'AWS Bedrock
  or equivalent' is a config change, not a rewrite."

---

## Fallback plan if something misbehaves on camera
- **LLM slow/unresponsive:** the narrative is cached after the first successful call — trigger it
  once during rehearsal so the recorded take hits the cache.
- **Retrain takes visibly long:** cut the wait in editing, or narrate over it — it's ~3–4s measured,
  should not be an issue.
- **Ollama not warm:** run the pre-warm curl command above 30 seconds before recording.
- **Queue has stale data:** run `scripts/seed_demo.sh` and restart the three services before the
  final take.
