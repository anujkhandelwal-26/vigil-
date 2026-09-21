import { useState } from 'react'
import { useSelector } from 'react-redux'
import {
  useListApplicationsQuery, useGetKpisQuery, useGetApplicationDetailQuery, useGetRingQuery,
  useLazyGetNarrativeQuery, useSubmitFeedbackMutation, useListModelsQuery,
  useGetCostCurveQuery, useRetrainModelMutation,
} from '../app/api'
import ActionBadge from '../components/ActionBadge'
import ReasonChips from '../components/ReasonChips'
import ShapWaterfall from '../components/ShapWaterfall'
import KpiTile from '../components/KpiTile'
import CopilotChat from '../components/CopilotChat'

function CaseDetail({ id, onFeedbackDone }) {
  const { data, isLoading } = useGetApplicationDetailQuery(id, { skip: !id })
  const { data: ringData } = useGetRingQuery(id, { skip: !id })
  const [getNarrative, narrativeState] = useLazyGetNarrativeQuery()
  const [submitFeedback, { isLoading: fbLoading }] = useSubmitFeedbackMutation()
  const [note, setNote] = useState('')

  if (!id) return <div className="card"><span className="faint">Select a case from the queue to see details.</span></div>
  if (isLoading || !data) return <div className="card">Loading case…</div>

  const app = data.application
  const decision = data.decision
  let shapTop = null
  try {
    shapTop = decision?.shapTop ? JSON.parse(decision.shapTop) : null
  } catch {
    shapTop = null
  }

  async function handleFeedback(verdict) {
    await submitFeedback({ id, verdict, note }).unwrap()
    setNote('')
    onFeedbackDone?.()
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>{app.externalRef}</h2>
        <ActionBadge action={decision?.action} />
      </div>

      {ringData?.ring && (
        <div className="card" style={{ background: 'rgba(224,90,90,0.1)', border: '1px solid var(--decline)', margin: '12px 0' }}>
          <strong style={{ color: 'var(--decline)' }}>🔗 Fraud ring detected</strong>
          <p className="muted" style={{ margin: '6px 0 0 0' }}>
            {ringData.ring.member_count} applications · detected via{' '}
            {ringData.ring.detection_method === 'behavioural_embedding_only'
              ? 'behavioural embedding similarity (no shared identifier)'
              : 'shared identifier + behavioural similarity'} ·
            {' '}₹{Number(ringData.ring.total_exposure_inr || 0).toLocaleString('en-IN')} distance-weighted exposure
          </p>
        </div>
      )}

      <div className="grid cols-3" style={{ marginTop: 12 }}>
        <div>
          <h3>Applicant</h3>
          <p className="muted">
            Age {app.age} · {app.employmentType} · ₹{Number(app.monthlyIncomeInr).toLocaleString('en-IN')}/mo<br />
            {app.residenceType} · Tier {app.cityTier} · PIN {app.pincodePrefix}xx
          </p>
          <h3>Loan</h3>
          <p className="muted">
            {app.product} · ₹{Number(app.amountInr).toLocaleString('en-IN')} · {app.tenureMonths}mo · {app.channel}
          </p>
        </div>
        <div>
          <h3>Device &amp; behaviour</h3>
          <p className="muted">
            Reused {app.deviceReuseCount30d}× (30d) · {app.isEmulator ? 'emulator' : 'real device'}<br />
            Form fill {app.formFillSeconds}s · {app.pasteEvents} paste events<br />
            IP apps (24h): {app.ipDistinctApps24h} {app.vpnOrProxy ? '· VPN/proxy' : ''}
          </p>
          <h3>Banking &amp; mobile</h3>
          <p className="muted">
            Penny-drop match {app.pennyDropNameMatch} · shared with {app.accountSharedWithNApplicants}<br />
            SIM swap (30d): {String(app.recentSimSwap30d)}
          </p>
        </div>
        <div>
          <h3>Score</h3>
          <p className="muted">
            Risk {decision ? Number(decision.riskScore).toFixed(3) : '—'}<br />
            Anomaly {decision?.anomalyScore != null ? Number(decision.anomalyScore).toFixed(3) : '—'}<br />
            Latency {decision?.latencyMs ?? '—'}ms · {decision?.modelVersion}
          </p>
        </div>
      </div>

      <h3 style={{ marginTop: 16 }}>Reason codes</h3>
      <ReasonChips codes={decision?.reasonCodes} />

      {shapTop && (
        <>
          <h3 style={{ marginTop: 16 }}>SHAP — top contributing signals</h3>
          <ShapWaterfall shapTop={shapTop} />
        </>
      )}

      <h3 style={{ marginTop: 16 }}>Analyst narrative</h3>
      {!narrativeState.data && (
        <button className="secondary" onClick={() => getNarrative(id)} disabled={narrativeState.isFetching}>
          {narrativeState.isFetching ? 'Generating…' : 'Generate narrative'}
        </button>
      )}
      {narrativeState.data && (
        <div>
          <p>{narrativeState.data.narrative}</p>
          <span className={`grounded-badge ${narrativeState.data.grounded ? '' : 'fallback'}`}>
            {narrativeState.data.grounded ? 'grounded ✓' : 'fallback template'} ·{' '}
            {narrativeState.data.provider}/{narrativeState.data.model} ·{' '}
            {narrativeState.data.cached ? 'cached' : `${narrativeState.data.latency_ms}ms`}
          </span>
        </div>
      )}

      <h3 style={{ marginTop: 16 }}>Copilot</h3>
      <CopilotChat applicationId={id} />

      <h3 style={{ marginTop: 16 }}>Verdict</h3>
      <div className="field" style={{ maxWidth: 400, marginBottom: 8 }}>
        <label>Note (optional)</label>
        <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="What did you see that the engine did not?" />
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button className="secondary danger" disabled={fbLoading} onClick={() => handleFeedback('FRAUD')}>Confirm Fraud</button>
        <button className="secondary success" disabled={fbLoading} onClick={() => handleFeedback('LEGIT')}>Mark Legitimate</button>
      </div>
    </div>
  )
}

export default function AnalystDashboard() {
  const role = useSelector((s) => s.auth.role)
  const [actionFilter, setActionFilter] = useState('ALL')
  const [selectedId, setSelectedId] = useState(null)
  const { data: kpis } = useGetKpisQuery(undefined, { pollingInterval: 4000 })
  const { data: queue, refetch } = useListApplicationsQuery({ action: actionFilter, limit: 100 }, { pollingInterval: 4000 })
  const { data: models } = useListModelsQuery()
  const { data: costCurve } = useGetCostCurveQuery()
  const [retrainModel, { isLoading: retraining }] = useRetrainModelMutation()
  const [retrainResult, setRetrainResult] = useState(null)

  async function handleRetrain() {
    setRetrainResult(null)
    try {
      const res = await retrainModel().unwrap()
      setRetrainResult(res)
    } catch (err) {
      setRetrainResult({ error: true, message: err?.data?.detail || 'Retrain failed.' })
    }
  }

  const byAction = Object.fromEntries((kpis?.byAction || []).map((r) => [r.action, r.n]))

  return (
    <div>
      <div className="grid cols-6" style={{ marginBottom: 16 }}>
        <KpiTile label="Decisions (24h)" value={kpis?.decisionsLast24h ?? '—'} />
        <KpiTile label="p95 latency" value={kpis ? `${Number(kpis.p95LatencyMs).toFixed(0)}ms` : '—'} />
        <KpiTile label="Approve" value={byAction.APPROVE ?? 0} />
        <KpiTile label="Step-up" value={byAction.STEP_UP ?? 0} />
        <KpiTile label="Review" value={byAction.REVIEW ?? 0} />
        <KpiTile label="Decline" value={byAction.DECLINE ?? 0} />
      </div>

      {costCurve && costCurve.four_way_decline_rate != null && (
        <div className="card" style={{ marginBottom: 16 }}>
          <h2>False-positive reduction — four actions, not two</h2>
          <p className="muted" style={{ marginTop: 0 }}>
            We didn't move the threshold. We added two more actions (STEP_UP, REVIEW) between
            approve and decline, so borderline applicants face friction instead of rejection.
          </p>
          <div className="grid cols-4">
            <div className="kpi-tile">
              <div className="label">Binary decline rate (t=0.5)</div>
              <div className="value">{(costCurve.naive_binary_decline_rate * 100).toFixed(2)}%</div>
            </div>
            <div className="kpi-tile">
              <div className="label">Four-way decline rate</div>
              <div className="value" style={{ color: 'var(--approve)' }}>
                {(costCurve.four_way_decline_rate * 100).toFixed(2)}%
              </div>
            </div>
            <div className="kpi-tile">
              <div className="label">Binary FP rate</div>
              <div className="value">{(costCurve.naive_binary_fp_rate * 100).toFixed(3)}%</div>
            </div>
            <div className="kpi-tile">
              <div className="label">Four-way FP rate</div>
              <div className="value" style={{ color: 'var(--approve)' }}>
                {(costCurve.four_way_fp_rate * 100).toFixed(3)}%
              </div>
            </div>
          </div>
          {costCurve.cost_assumptions_inr && (
            <p className="faint" style={{ marginTop: 10 }}>
              Cost assumptions: ₹{costCurve.cost_assumptions_inr.C_FN.toLocaleString('en-IN')} per missed
              fraud · ₹{costCurve.cost_assumptions_inr.C_FP.toLocaleString('en-IN')} per wrongly-declined
              good customer · ₹{costCurve.cost_assumptions_inr.C_STEPUP} step-up friction ·
              ₹{costCurve.cost_assumptions_inr.C_REVIEW} analyst review.
              Thresholds: low={Number(costCurve.thresholds?.low).toFixed(2)},
              high={Number(costCurve.thresholds?.high).toFixed(2)},
              decline={Number(costCurve.thresholds?.decline).toFixed(2)} ({costCurve.model_version}).
            </p>
          )}
          {costCurve.fairness && (
            <>
              <h3 style={{ marginTop: 16 }}>Fairness — disparate-impact ratio (80% rule)</h3>
              <div className="grid cols-4">
                {Object.entries(costCurve.fairness).flatMap(([group, rows]) =>
                  Object.entries(rows).map(([label, v]) => (
                    <div className="kpi-tile" key={`${group}-${label}`}>
                      <div className="label">{group}: {label}</div>
                      <div className="value" style={{ fontSize: 18 }}>
                        {(v.disparate_impact_ratio * 100).toFixed(1)}%
                      </div>
                      <div className="sub">n={v.n} · approval {(v.approval_rate * 100).toFixed(1)}%</div>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
        </div>
      )}

      <div className="grid cols-2">
        <div>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ margin: 0 }}>Queue</h2>
              <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} style={{ background: 'var(--panel-2)', color: 'var(--ink)', border: '1px solid var(--border)', borderRadius: 6, padding: '6px 10px' }}>
                <option value="ALL">All actions</option>
                <option value="DECLINE">Decline</option>
                <option value="REVIEW">Review</option>
                <option value="STEP_UP">Step-up</option>
                <option value="APPROVE">Approve</option>
              </select>
            </div>
            <table>
              <thead>
                <tr><th>Ref</th><th>Product</th><th>Amount</th><th>Action</th><th>Score</th><th>Latency</th></tr>
              </thead>
              <tbody>
                {(queue || []).map((a) => (
                  <tr key={a.id} onClick={() => setSelectedId(a.id)}>
                    <td className="mono">{a.externalRef}</td>
                    <td>{a.product}</td>
                    <td>₹{Number(a.amountInr).toLocaleString('en-IN')}</td>
                    <td><ActionBadge action={a.action} /></td>
                    <td>{a.riskScore != null ? Number(a.riskScore).toFixed(2) : '—'}</td>
                    <td>{a.latencyMs ?? '—'}ms</td>
                  </tr>
                ))}
                {(!queue || queue.length === 0) && (
                  <tr><td colSpan={6} className="faint">No applications yet — submit one from the Application tab.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ margin: 0 }}>Model registry</h2>
              {role === 'ADMIN' ? (
                <button className="secondary" onClick={handleRetrain} disabled={retraining}>
                  {retraining ? 'Retraining…' : 'Retrain from feedback'}
                </button>
              ) : (
                <span className="faint">Retrain requires ADMIN role</span>
              )}
            </div>
            {retrainResult && !retrainResult.error && (
              <p className={retrainResult.promoted ? 'muted' : 'faint'} style={{ marginTop: 8 }}>
                <strong style={{ color: retrainResult.promoted ? 'var(--approve)' : 'var(--stepup)' }}>
                  {retrainResult.version}
                </strong>
                {' '}— {retrainResult.promoted_reason} (trained on {retrainResult.training_rows} rows,
                {' '}{retrainResult.feedback_rows_used} from analyst feedback, in {retrainResult.train_seconds}s)
              </p>
            )}
            {retrainResult?.error && (
              <p className="error-text" style={{ marginTop: 8 }}>{retrainResult.message}</p>
            )}
            {models && models.length > 0 ? (
              <table>
                <thead><tr><th>Version</th><th>Algorithm</th><th>PR-AUC</th><th>Recall@1%FPR</th><th>Active</th></tr></thead>
                <tbody>
                  {models.map((m) => (
                    <tr key={m.id}>
                      <td className="mono">{m.version}</td>
                      <td>{m.algorithm}</td>
                      <td>{m.prAuc}</td>
                      <td>{m.recallAt1pctFpr}</td>
                      <td>{m.active ? '✓' : ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <span className="faint">No registered model versions yet.</span>
            )}
          </div>
        </div>

        <CaseDetail id={selectedId} onFeedbackDone={refetch} />
      </div>
    </div>
  )
}
