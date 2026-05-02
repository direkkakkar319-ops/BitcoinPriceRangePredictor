import {
  ComposedChart, Line, Area, XAxis, YAxis,
  Tooltip, ReferenceLine, ResponsiveContainer, CartesianGrid,
} from 'recharts'

const fmt = (n) => n?.toLocaleString('en-US', { maximumFractionDigits: 0 })

function TooltipBox({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const row = payload[0].payload
  return (
    <div className="bg-panel border border-line rounded-lg px-3 py-2 text-xs tabular">
      <div className="text-mute mb-1">{new Date(label).toUTCString().slice(5, 22)} UTC</div>
      {row.close != null && <div>close <span className="text-btc ml-2">${fmt(row.close)}</span></div>}
      {row.lo != null && <div>range <span className="text-band ml-2">${fmt(row.lo)} – ${fmt(row.hi)}</span></div>}
    </div>
  )
}

export default function PredictionChart({ bars, lo, hi, lastBarTime, nextBarTime, currentPrice }) {
  const data = bars.map((b) => ({
    t: new Date(b.open_time).getTime(),
    close: b.close,
  }))

  // shaded forecast cone — degenerate at last bar, opens to [lo, hi] at next bar
  const lastT = new Date(lastBarTime).getTime()
  const nextT = new Date(nextBarTime).getTime()
  data.push({ t: lastT, close: currentPrice, lo: currentPrice, hi: currentPrice })
  data.push({ t: nextT, lo, hi })

  const closes = bars.map((b) => b.close)
  const yMin = Math.min(...closes, lo) * 0.998
  const yMax = Math.max(...closes, hi) * 1.002

  return (
    <ResponsiveContainer width="100%" height={380}>
      <ComposedChart data={data} margin={{ top: 10, right: 16, left: 8, bottom: 0 }}>
        <defs>
          <linearGradient id="band" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#60A5FA" stopOpacity={0.35} />
            <stop offset="100%" stopColor="#60A5FA" stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#1F242B" vertical={false} />
        <XAxis
          dataKey="t"
          type="number"
          domain={['dataMin', 'dataMax']}
          scale="time"
          tickFormatter={(t) => new Date(t).toUTCString().slice(17, 22)}
          stroke="#8A95A1"
          tick={{ fontSize: 11 }}
        />
        <YAxis
          domain={[yMin, yMax]}
          tickFormatter={(v) => `$${fmt(v)}`}
          stroke="#8A95A1"
          tick={{ fontSize: 11 }}
          width={70}
        />
        <Tooltip content={<TooltipBox />} />
        <Area
          type="linear"
          dataKey="hi"
          stroke="#60A5FA"
          strokeOpacity={0.6}
          strokeWidth={1}
          fill="url(#band)"
          isAnimationActive={false}
          connectNulls
        />
        <Area
          type="linear"
          dataKey="lo"
          stroke="#60A5FA"
          strokeOpacity={0.6}
          strokeWidth={1}
          fill="#0B0D10"
          isAnimationActive={false}
          connectNulls
        />
        <Line
          type="monotone"
          dataKey="close"
          stroke="#F7931A"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
        <ReferenceLine x={lastT} stroke="#2A323A" strokeDasharray="3 3" />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
