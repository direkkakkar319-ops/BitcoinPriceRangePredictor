export default function MetricCard({ label, value, sub, accent }) {
  return (
    <div className="bg-panel border border-line rounded-xl p-4">
      <div className="text-xs uppercase tracking-wider text-mute">{label}</div>
      <div className={`mt-2 text-2xl font-semibold tabular ${accent || 'text-ink'}`}>
        {value}
      </div>
      {sub && <div className="mt-1 text-xs text-mute tabular">{sub}</div>}
    </div>
  )
}
