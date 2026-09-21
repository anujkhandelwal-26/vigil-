/** Decision actions carry meaning, so they are labelled as well as coloured. */
const ACTION_STYLE = {
  APPROVE:  { bg: '#e6f0ea', fg: 'var(--color-a-approve)', label: 'Approve' },
  STEP_UP:  { bg: '#fbf0e4', fg: 'var(--color-a-stepup)', label: 'Step-up' },
  REVIEW:   { bg: '#e8eef6', fg: 'var(--color-a-review)', label: 'Review' },
  DECLINE:  { bg: '#f8e9e5', fg: 'var(--color-a-decline)', label: 'Decline' },
}

export function ActionChip({ action, size = 'md' }) {
  if (!action) return null
  const style = ACTION_STYLE[action] || { bg: '#e7ebe6', fg: 'var(--color-ink-muted)', label: action }
  return (
    <span
      className={`inline-flex items-center rounded-sm font-medium ${
        size === 'sm' ? 'px-1.5 py-0.5 text-[11px]' : 'px-2 py-1 text-xs'
      }`}
      style={{ background: style.bg, color: style.fg }}
    >
      {style.label}
    </span>
  )
}

export function Panel({ title, action, children, className = '' }) {
  return (
    <section className={`border border-rule bg-surface ${className}`}>
      {title && (
        <header className="flex items-center justify-between border-b border-rule-soft px-4 py-2.5">
          <h2 className="text-[13px] font-semibold text-ink">{title}</h2>
          {action}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  )
}

export function Field({ label, children, muted = false }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1.5">
      <dt className={`text-[13px] ${muted ? 'text-ink-faint' : 'text-ink-muted'}`}>{label}</dt>
      <dd className="tnum text-[13px] font-medium text-ink text-right">{children}</dd>
    </div>
  )
}

export function Button({ children, variant = 'secondary', className = '', ...rest }) {
  const styles = {
    primary: 'bg-signal text-white hover:bg-[#1d3372] disabled:bg-ink-faint',
    secondary: 'border border-rule bg-surface text-ink hover:bg-paper disabled:text-ink-faint',
    danger: 'border border-[#e3c2b6] bg-[#fdf4f1] text-[#9c3211] hover:bg-[#fae9e3]',
    success: 'border border-[#bcdccb] bg-[#f2f8f4] text-[#14603f] hover:bg-[#e6f0ea]',
  }[variant]
  return (
    <button
      {...rest}
      className={`rounded-sm px-3 py-1.5 text-[13px] font-medium transition-colors disabled:cursor-not-allowed ${styles} ${className}`}
    >
      {children}
    </button>
  )
}

export function Chip({ children, title }) {
  return (
    <span
      title={title}
      className="mr-1.5 mb-1.5 inline-block rounded-sm border border-rule bg-paper px-2 py-1 text-[11px] text-ink-muted"
    >
      {children}
    </span>
  )
}

export function Empty({ children }) {
  return <p className="py-8 text-center text-[13px] text-ink-faint">{children}</p>
}

export function Label({ label, children, className = '' }) {
  return (
    <label className={`block ${className}`}>
      <span className="text-[12px] text-ink-muted">{label}</span>
      {children}
    </label>
  )
}

export const inputClass = 'mt-1 w-full border border-rule bg-surface px-2.5 py-2 text-[13px]'
