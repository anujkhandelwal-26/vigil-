// Plain CSS bar list instead of a chart library waterfall -- deliberately
// simple, fast to render, and unambiguous about direction (red = toward
// fraud, green = away from it), matching the SHAP contribution sign.
export default function ShapWaterfall({ shapTop }) {
  if (!shapTop || shapTop.length === 0) {
    return <span className="faint">No SHAP explanation available for this decision.</span>
  }
  const maxAbs = Math.max(...shapTop.map((s) => Math.abs(s.contribution)), 0.0001)
  return (
    <div>
      {shapTop.map((s, i) => {
        const pct = Math.min(100, (Math.abs(s.contribution) / maxAbs) * 100)
        const up = s.direction === 'increases_risk'
        return (
          <div className="shap-row" key={i}>
            <span className="mono" title={s.feature}>{s.feature}</span>
            <div className="shap-bar-track">
              <div
                className={`shap-bar-fill ${up ? 'up' : 'down'}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="mono faint">{s.contribution > 0 ? '+' : ''}{s.contribution.toFixed(3)}</span>
          </div>
        )
      })}
    </div>
  )
}
