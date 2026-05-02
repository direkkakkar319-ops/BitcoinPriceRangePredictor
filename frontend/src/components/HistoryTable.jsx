const fmt = (n) => n?.toLocaleString('en-US', { maximumFractionDigits: 0 })

export default function HistoryTable({ rows }) {
  if (!rows?.length) return null

  return (
    <div className="bg-panel border border-line rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-line text-sm font-medium">
        Prediction history
      </div>
      <div className="max-h-96 overflow-y-auto">
        <table className="w-full text-sm tabular">
          <thead className="text-mute text-xs uppercase tracking-wider sticky top-0 bg-panel">
            <tr>
              <th className="text-left px-4 py-2 font-medium">Bar</th>
              <th className="text-right px-4 py-2 font-medium">Lo</th>
              <th className="text-right px-4 py-2 font-medium">Hi</th>
              <th className="text-right px-4 py-2 font-medium">Actual</th>
              <th className="text-center px-4 py-2 font-medium">Hit</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const t = r.next_bar_time.slice(0, 16).replace('T', ' ')
              const hit = r.actual == null ? null : r.lo <= r.actual && r.actual <= r.hi
              return (
                <tr key={r.next_bar_time} className="border-t border-line/60">
                  <td className="px-4 py-2 text-mute">{t}</td>
                  <td className="px-4 py-2 text-right">${fmt(r.lo)}</td>
                  <td className="px-4 py-2 text-right">${fmt(r.hi)}</td>
                  <td className="px-4 py-2 text-right">
                    {r.actual == null ? <span className="text-mute">—</span> : `$${fmt(r.actual)}`}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {hit == null
                      ? <span className="text-mute">·</span>
                      : hit
                        ? <span className="text-up">✓</span>
                        : <span className="text-down">✗</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
