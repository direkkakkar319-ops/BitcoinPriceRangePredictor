# BTC 1-Hour Forecaster — Workflow

## What this is

A Bitcoin price forecaster for the AlphaI × Polaris challenge. Predicts the **95% range** for BTC's next 1-hour close, not a point estimate. Two consumers share the same model: an offline 30-day backtest (`backtest.py`) and a live React dashboard backed by a FastAPI service.

Model: Geometric Brownian Motion + Student-t innovations on a rolling 72-bar volatility window. Data: Binance public klines (no API key).

**Stack**
- Backend: Python · FastAPI · NumPy · SciPy · Pandas · requests
- Frontend: React 18 · Vite · Tailwind · Recharts

---

## Layout

```
alphaai/
├── data.py                     # Binance fetcher
├── model.py                    # GBM + Student-t — predict_range()
├── backtest.py                 # 30-day walk-forward → backtest_results.jsonl + metrics.json
├── main.py                     # FastAPI: /api/state
├── app.py                      # legacy Streamlit dashboard (still works)
├── requirements.txt
├── backtest_results.jsonl      # 720 predictions (graded artifact)
├── metrics.json                # coverage / avg_width / winkler
├── predictions_log.jsonl       # Part C — appended on each /api/state hit
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   ├── main.jsx
    │   ├── index.css
    │   └── components/
    │       ├── MetricCard.jsx
    │       ├── PredictionChart.jsx
    │       └── HistoryTable.jsx
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── postcss.config.js
```

Python at the root, React under `frontend/`. Two deploys, one repo.

---

## Architecture

```
                 ┌─────────────┐
                 │ Binance API │
                 └──────┬──────┘
                        │
                  data.py (fetch klines)
                        │
              ┌─────────┴────────┐
              │                  │
        backtest.py          main.py (FastAPI)
              │                  │
   backtest_results.jsonl   /api/state  ◄──── React (Vite + Tailwind)
   metrics.json                  │             ├ MetricCard
                                 │             ├ PredictionChart (Recharts)
                          predictions_log.jsonl└ HistoryTable
```

The model lives in **one place** (`model.py:predict_range`) and both flows call it. That's the whole point — the live dashboard cannot drift from what the backtest measured.

---

## Files that matter

### `model.py`
`predict_range(closes)` → `(lo, hi)`. Fits Student-t on the last 72 log-returns, simulates 10k draws, returns the 2.5/97.5 percentiles of the simulated next-bar prices. `df` clamped to [2.1, 50] for numerical sanity.

### `data.py`
`fetch_btc(limit, end_time=None)` — single GET to `/api/v3/klines`, returns a clean DataFrame sorted by time.

### `backtest.py`
Walk-forward over 720 bars. Critical line:
```python
lo, hi = predict_range(closes[:i])   # only data BEFORE bar i
preds.append({..., "actual": closes[i]})
```
The slice `[:i]` is the no-peeking guarantee. Writes `backtest_results.jsonl` + `metrics.json`.

### `main.py` — FastAPI
One endpoint: `GET /api/state` returns everything the UI needs in a single shot.

```jsonc
{
  "current_price": 67234.50,
  "lo": 67100.00, "hi": 67450.00,
  "last_bar_time": "...", "next_bar_time": "...",
  "bars":   [{open_time, open, high, low, close}, ...],   // last 50
  "metrics": { "coverage": 0.95, "avg_width": 380, "winkler": 410 },
  "history": [{predicted_at, next_bar_time, lo, hi, actual}, ...]
}
```

On every call it:
1. Pulls the last ~500 closed bars (60s in-process cache so we don't hammer Binance).
2. Runs `predict_range()`.
3. Back-fills `actual` for any past predictions whose target hour has now closed.
4. Appends a new prediction for `next_bar_time` if it's not already logged.

CORS is wide-open — fine for this challenge, lock down `allow_origins` in production.

### `frontend/src/App.jsx`
Single fetcher, single state object. Polls `/api/state` every 60 seconds. Three panels: backtest headline, live prediction cards, chart with forecast cone, history table.

### `frontend/src/components/PredictionChart.jsx`
Recharts `ComposedChart`. Trick: the `lo`/`hi` Areas only have data for the last historical bar (degenerate — both equal `current_price`) and the next bar (`lo`, `hi`). That's how Recharts draws a triangular forecast cone fanning out from "now" to the next close.

### `frontend/src/components/HistoryTable.jsx` & `MetricCard.jsx`
Dumb display components. History rows show `✓` / `✗` / `·` based on whether `actual` is set and inside the predicted range.

---

## A walk through one request

User opens the dashboard at 14:23 UTC.

1. **React** mounts → `useEffect` calls `fetchState()` → `GET /api/state`.
2. **FastAPI** receives the request:
   - `get_bars()` — cache miss → `data.py:fetch_btc(limit=502)` → drop the open bar → 501 closed bars.
   - `predict_range(closes[-500:])` — fits t-distribution on last 72 returns, Monte Carlo, returns `(67100, 67450)`.
   - Lock the log, back-fill any matured `actual` values, append the new prediction for `next_bar_time = 15:00`, write the file.
   - Read `metrics.json` for headline metrics.
   - Slice last 50 bars for the chart, return JSON.
3. **React** stashes the response in state and renders. The chart fans out a blue cone from the last close to the predicted `[lo, hi]` at the next close.
4. 60 seconds later, `setInterval` fires another request. If the hour has rolled over, the new bar shows up, the previous prediction's `actual` gets filled, and a fresh prediction is logged.

---

## Running it locally

**Backend:**
```bash
pip install -r requirements.txt
python backtest.py                              # one time — generates metrics.json + backtest_results.jsonl
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev                                     # http://localhost:5173
```

Vite proxies `/api/*` → `localhost:8000` so you don't fight CORS in dev.

---

## Deploying

**Backend → Render** (free tier, has persistent disk):
- New Web Service, point at this repo
- Build: `pip install -r requirements.txt && python backtest.py`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Note the URL, e.g. `https://alphaai-api.onrender.com`

**Frontend → Vercel**:
- Import repo, set **Root Directory = `frontend`**
- Env var: `VITE_API_URL=https://alphaai-api.onrender.com`
- Build: `npm run build` · Output: `dist`

Render's free tier sleeps after 15 min idle — first request after sleep takes ~30s. For a graded demo that's fine; bump to a paid tier or use Fly.io if you want always-on.

`predictions_log.jsonl` lives on Render's disk. On free Render that disk *is* persistent across restarts, but if you ever rebuild it gets wiped. Good enough for the challenge — for real production you'd swap it for Postgres or S3.

---

## Mental model

```
predict_range()  ◄── single source of truth (model.py)
      ▲
      ├── backtest.py loops over history → writes JSONL + metrics
      └── main.py wraps it in HTTP → React renders it
```

To improve the score, work in `model.py` only — try EWMA volatility, GARCH, or a regime switch. Don't touch the slice `closes[:i]` in `backtest.py` — that's the leakage guarantee.

---

## Where to start reading

1. `model.py` (~25 lines) — the actual forecasting logic.
2. `backtest.py` — see the no-peeking loop.
3. `main.py` — see how the API wraps the model.
4. `frontend/src/App.jsx` — single component, top to bottom.
5. `frontend/src/components/PredictionChart.jsx` — only weird bit is the two-point cone.
