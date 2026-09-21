import { useState } from 'react'
import { SCENARIOS } from '../data/scenarios'
import { useSubmitApplicationMutation } from '../app/api'
import ActionBadge from '../components/ActionBadge'
import ReasonChips from '../components/ReasonChips'
import ShapWaterfall from '../components/ShapWaterfall'

const FIELDS = [
  // block, key, label, type
  ['Applicant', 'age', 'Age', 'number'],
  ['Applicant', 'gender', 'Gender', 'select', ['M', 'F']],
  ['Applicant', 'employmentType', 'Employment type', 'select', ['SALARIED', 'SELF_EMPLOYED', 'GIG_WORKER', 'UNEMPLOYED_STUDENT']],
  ['Applicant', 'monthlyIncomeInr', 'Monthly income (₹)', 'number'],
  ['Applicant', 'cityTier', 'City tier', 'select', [1, 2, 3]],
  ['Applicant', 'pincodePrefix', 'Pincode prefix', 'text'],
  ['Applicant', 'residenceType', 'Residence type', 'select', ['OWNED', 'RENTED', 'FAMILY']],

  ['Loan', 'product', 'Product', 'select', ['CONSUMER_DURABLE', 'PERSONAL', 'TWO_WHEELER', 'EDUCATION_TOPUP']],
  ['Loan', 'amountInr', 'Amount (₹)', 'number'],
  ['Loan', 'tenureMonths', 'Tenure (months)', 'number'],
  ['Loan', 'channel', 'Channel', 'select', ['ANDROID_APP', 'IOS_APP', 'WEB', 'PARTNER_POS']],

  ['Bureau', 'cibilScore', 'CIBIL score', 'number'],
  ['Bureau', 'isNewToCredit', 'New to credit', 'boolean'],
  ['Bureau', 'activeLoans', 'Active loans', 'number'],
  ['Bureau', 'enquiries30d', 'Enquiries (30d)', 'number'],
  ['Bureau', 'maxDpd12m', 'Max DPD (12m)', 'number'],
  ['Bureau', 'creditUtilisationPct', 'Credit utilisation %', 'number'],
  ['Bureau', 'oldestAccountMonths', 'Oldest account (months)', 'number'],

  ['KYC', 'panFormatValid', 'PAN format valid', 'boolean'],
  ['KYC', 'panNameMatchScore', 'PAN name match (0-1)', 'number'],
  ['KYC', 'aadhaarPanLinked', 'Aadhaar–PAN linked', 'boolean'],
  ['KYC', 'nameDobMismatch', 'Name/DOB mismatch', 'boolean'],
  ['KYC', 'digilockerDocsFetched', 'DigiLocker docs fetched', 'number'],
  ['KYC', 'aadhaarLast4', 'Aadhaar last 4 digits', 'text'],

  ['Device', 'deviceHash', 'Device hash', 'text'],
  ['Device', 'deviceReuseCount30d', 'Device reuse count (30d)', 'number'],
  ['Device', 'isEmulator', 'Emulator', 'boolean'],
  ['Device', 'isRooted', 'Rooted', 'boolean'],
  ['Device', 'appInstallAgeDays', 'App install age (days)', 'number'],
  ['Device', 'ipPrefix', 'IP prefix', 'text'],
  ['Device', 'ipDistinctApps24h', 'IP distinct apps (24h)', 'number'],
  ['Device', 'ipPincodeDistanceKm', 'IP-pincode distance (km)', 'number'],
  ['Device', 'vpnOrProxy', 'VPN / proxy', 'boolean'],

  ['Behaviour', 'formFillSeconds', 'Form fill time (s)', 'number'],
  ['Behaviour', 'typingSpeedCpm', 'Typing speed (cpm)', 'number'],
  ['Behaviour', 'pasteEvents', 'Paste events', 'number'],
  ['Behaviour', 'fieldCorrections', 'Field corrections', 'number'],
  ['Behaviour', 'sessionScreens', 'Session screens', 'number'],
  ['Behaviour', 'nightApplication', 'Night application', 'boolean'],
  ['Behaviour', 'timeSincePrevAppHours', 'Hours since prev. application', 'number'],

  ['Banking', 'bankAccountHash', 'Bank account hash', 'text'],
  ['Banking', 'pennyDropNameMatch', 'Penny-drop name match (0-1)', 'number'],
  ['Banking', 'accountAgeMonths', 'Account age (months)', 'number'],
  ['Banking', 'avgMonthlyCreditInr', 'Avg monthly credit (₹)', 'number'],
  ['Banking', 'salaryCreditRegularity', 'Salary credit regularity (0-1)', 'number'],
  ['Banking', 'bounceCount6m', 'Bounce count (6m)', 'number'],
  ['Banking', 'accountSharedWithNApplicants', 'Account shared with N applicants', 'number'],

  ['Mobile', 'mobileHash', 'Mobile hash', 'text'],
  ['Mobile', 'mobileAgeOnNetworkDays', 'Mobile age on network (days)', 'number'],
  ['Mobile', 'recentSimSwap30d', 'Recent SIM swap (30d)', 'boolean'],
  ['Mobile', 'mobileNameMatch', 'Mobile owner name match (0-1)', 'number'],
]

const BLOCKS = [...new Set(FIELDS.map((f) => f[0]))]

function Field({ block, k, label, type, options, value, onChange }) {
  if (type === 'boolean') {
    return (
      <div className="field">
        <label>{label}</label>
        <select value={String(value)} onChange={(e) => onChange(k, e.target.value === 'true')}>
          <option value="true">true</option>
          <option value="false">false</option>
        </select>
      </div>
    )
  }
  if (type === 'select') {
    return (
      <div className="field">
        <label>{label}</label>
        <select value={value ?? ''} onChange={(e) => onChange(k, e.target.value)}>
          {options.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      </div>
    )
  }
  return (
    <div className="field">
      <label>{label}</label>
      <input
        type={type === 'number' ? 'number' : 'text'}
        value={value ?? ''}
        onChange={(e) => onChange(k, type === 'number' ? (e.target.value === '' ? null : Number(e.target.value)) : e.target.value)}
      />
    </div>
  )
}

export default function ApplyDashboard() {
  const [scenarioKey, setScenarioKey] = useState('CLEAN')
  const [form, setForm] = useState(() => SCENARIOS.CLEAN.build())
  const [submitApplication, { isLoading }] = useSubmitApplicationMutation()
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  function applyScenario(key) {
    setScenarioKey(key)
    setForm(SCENARIOS[key].build())
    setResult(null)
    setError(null)
  }

  function updateField(k, v) {
    setForm((f) => ({ ...f, [k]: v }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setResult(null)
    const t0 = performance.now()
    try {
      const res = await submitApplication(form).unwrap()
      // Don't mutate the response -- RTK Query freezes cached response objects in
      // dev mode to catch exactly this kind of bug.
      setResult({ ...res, _clientRoundTripMs: Math.round(performance.now() - t0) })
    } catch (err) {
      setError(err?.data?.detail || 'Submission failed — check the field values.')
    }
  }

  let shapTop = null
  try {
    shapTop = result?.shapTop ? JSON.parse(result.shapTop) : null
  } catch {
    shapTop = null
  }

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h1>Loan Application</h1>
          <div className="field" style={{ minWidth: 260 }}>
            <label>Scenario (prefills, all editable)</label>
            <select value={scenarioKey} onChange={(e) => applyScenario(e.target.value)}>
              {Object.entries(SCENARIOS).map(([k, s]) => (
                <option key={k} value={k}>{s.label}</option>
              ))}
            </select>
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="field" style={{ maxWidth: 320, marginBottom: 16 }}>
            <label>Application reference</label>
            <input value={form.externalRef} onChange={(e) => updateField('externalRef', e.target.value)} />
          </div>

          {BLOCKS.map((block) => (
            <fieldset key={block}>
              <legend>{block}</legend>
              <div className="form-grid">
                {FIELDS.filter((f) => f[0] === block).map(([, k, label, type, options]) => (
                  <Field key={k} block={block} k={k} label={label} type={type} options={options}
                         value={form[k]} onChange={updateField} />
                ))}
              </div>
            </fieldset>
          ))}

          <button className="primary" type="submit" disabled={isLoading}>
            {isLoading ? 'Scoring…' : 'Submit application'}
          </button>
        </form>
      </div>

      {error && (
        <div className="card">
          <span className="error-text">{typeof error === 'string' ? error : JSON.stringify(error)}</span>
        </div>
      )}

      {result && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <h2 style={{ margin: 0 }}>Decision</h2>
            <ActionBadge action={result.action} />
          </div>
          <div className="grid cols-4" style={{ marginBottom: 16 }}>
            <div className="kpi-tile">
              <div className="label">Risk score (supervised)</div>
              <div className="value">{Number(result.riskScore).toFixed(3)}</div>
            </div>
            <div className="kpi-tile">
              <div className="label">Anomaly score (novelty)</div>
              <div className="value" style={{ color: result.anomalyScore != null && Number(result.anomalyScore) > 0.85 ? 'var(--decline)' : undefined }}>
                {result.anomalyScore != null ? Number(result.anomalyScore).toFixed(3) : '—'}
              </div>
            </div>
            <div className="kpi-tile">
              <div className="label">Server latency</div>
              <div className="value">{result.latencyMs}ms</div>
              <div className="sub">round-trip {result._clientRoundTripMs}ms</div>
            </div>
            <div className="kpi-tile">
              <div className="label">Degraded</div>
              <div className="value" style={{ fontSize: 16, color: result.degraded ? 'var(--decline)' : 'var(--approve)' }}>
                {result.degraded ? 'yes (rules-only)' : 'no'}
              </div>
            </div>
          </div>

          {result.anomalyScore != null && Number(result.anomalyScore) > 0.85 && Number(result.riskScore) < 0.15 && (
            <div className="card" style={{ background: 'rgba(224,90,90,0.1)', border: '1px solid var(--decline)', marginBottom: 16 }}>
              <strong style={{ color: 'var(--decline)' }}>⚠ NOVEL PATTERN DETECTED</strong>
              <p className="muted" style={{ margin: '6px 0 0 0' }}>
                The supervised model scores this application as low-risk ({Number(result.riskScore).toFixed(3)}) —
                it has never seen this behavioural signature in training. But the unsupervised novelty
                channel flags it as highly anomalous ({Number(result.anomalyScore).toFixed(3)}). This is
                exactly the gap a purely supervised system would miss: a fraud typology the model was
                never trained on. Route to REVIEW and use the copilot / feedback loop to confirm and retrain.
              </p>
            </div>
          )}

          <h3>Reason codes</h3>
          <ReasonChips codes={result.reasonCodes} />

          {shapTop && (
            <>
              <h3 style={{ marginTop: 16 }}>Top contributing signals</h3>
              <ShapWaterfall shapTop={shapTop} />
            </>
          )}

          {result.action === 'STEP_UP' && result.verificationSteps?.length > 0 && (
            <>
              <h3 style={{ marginTop: 16 }}>Verification required (Indian step-up ladder)</h3>
              <ol>
                {result.verificationSteps.map((s) => <li key={s}>{s}</li>)}
              </ol>
            </>
          )}

          {result.action === 'APPROVE' && result.keyFactStatement && (
            <>
              <h3 style={{ marginTop: 16 }}>Key Fact Statement (RBI Digital Lending Directions, 2025)</h3>
              <p className="muted">{result.keyFactStatement}</p>
            </>
          )}
        </div>
      )}
    </div>
  )
}
