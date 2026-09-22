export default function KpiTile({ label, value, sub }) {
  return (
    <div className="border border-rule bg-surface p-3.5">
      <div className="text-[11px] uppercase tracking-wide text-ink-faint">{label}</div>
      <div className="tnum mt-1 text-[22px] font-semibold leading-none text-ink">{value}</div>
      {sub && <div className="mt-1 text-[11px] text-ink-faint">{sub}</div>}
    </div>
  )
}
