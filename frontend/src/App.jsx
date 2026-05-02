import { useEffect, useState } from 'react'
import { fetchState } from './api'
import MetricCard from './components/MetricCard'
import PredictionChart from './components/PredictionChart'
import HistoryTable from './components/HistoryTable'

const fmt = (n) => n?.toLocaleString('en-US', { maximumFractionDigits: 2 })
const fmt0 = (n) => n?.toLocaleString('en-US', { maximumFractionDigits: 0 })

export default function App() {
  const [state, setState] = useState(null)
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)

  const load = async () => {
    try {
      setErr(null)
      const s = await fetchState()
      setState(s)
    } catch (e) {
      setErr(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 60_000)
    return () => clearInterval(id)
  }, [])

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-mute">Loading…</div>
  }

  if (err || !state) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-3">
        <div className="text-down">Failed to load: {err}</div>
        <button onClick={load} className="px-3 py-1.5 bg-panel border border-line rounded-md text-sm">
          Retry
        </button>
      </div>
    )
  }

  const { current_price, lo, hi, last_bar_time, next_bar_time, bars, metrics, history } = state
  const width = hi - lo
  const widthPct = (width / current_price) * 100

  return (
    <div className="min-h-screen">
      <header className="border-b border-line">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-btc/15 flex items-center justify-center text-btc font-bold">₿</div>
            <div>
              <div className="text-base font-semibold">BTC · Next Hour Forecast</div>
              <div className="text-xs text-mute">GBM + Student-t · AlphaI × Polaris</div>
            </div>
          </div>
          <button
            onClick={load}
            className="text-xs px-3 py-1.5 bg-panel border border-line rounded-md hover:border-mute transition-colors"
          >
            Refresh
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6 space-y-6">
        {/* backtest headline */}
        {metrics && (
          <div>
            <div className="text-xs uppercase tracking-wider text-mute mb-2">30-day backtest</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <MetricCard
                label="Coverage"
                value={`${(metrics.coverage * 100).toFixed(1)}%`}
                sub="target 95.0%"
                accent={Math.abs(metrics.coverage - 0.95) < 0.02 ? 'text-up' : 'text-ink'}
              />
              <MetricCard
                label="Avg width"
                value={`$${fmt0(metrics.avg_width)}`}
                sub="lower is better"
              />
              <MetricCard
                label="Winkler"
                value={fmt0(metrics.winkler)}
                sub="lower is better"
              />
            </div>
          </div>
        )}

        {/* live prediction */}
        <div>
          <div className="flex items-baseline justify-between mb-2">
            <div className="text-xs uppercase tracking-wider text-mute">Live prediction</div>
            <div className="text-xs text-mute tabular">
              next close · {new Date(next_bar_time).toUTCString().slice(17, 22)} UTC
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <MetricCard label="BTC now" value={`$${fmt(current_price)}`} accent="text-btc" />
            <MetricCard label="Lower (95%)" value={`$${fmt(lo)}`} accent="text-band" />
            <MetricCard label="Upper (95%)" value={`$${fmt(hi)}`} accent="text-band" />
            <MetricCard
              label="Range width"
              value={`$${fmt0(width)}`}
              sub={`${widthPct.toFixed(2)}% of price`}
            />
          </div>
        </div>

        {/* chart */}
        <div className="bg-panel border border-line rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium">Last 50 bars · 95% forecast cone</div>
            <div className="flex items-center gap-4 text-xs text-mute">
              <span className="flex items-center gap-1.5"><span className="w-3 h-0.5 bg-btc inline-block" />price</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-2 bg-band/30 inline-block rounded-sm" />95% range</span>
            </div>
          </div>
          <PredictionChart
            bars={bars}
            lo={lo}
            hi={hi}
            lastBarTime={last_bar_time}
            nextBarTime={next_bar_time}
            currentPrice={current_price}
          />
        </div>

        {/* history */}
        <HistoryTable rows={history} />

        <footer className="text-xs text-mute text-center pt-4 pb-8">
          Auto-refresh every 60s · Data: Binance public API · {new Date().toUTCString().slice(5, 22)} UTC
        </footer>
      </main>
    </div>
  )
}
