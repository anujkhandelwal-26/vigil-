export default function ActionBadge({ action }) {
  if (!action) return null
  return <span className={`badge ${action}`}>{action.replace('_', ' ')}</span>
}
