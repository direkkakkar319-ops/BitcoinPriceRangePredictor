import json
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import fetch_btc
from model import predict_range

LOG = "predictions_log.jsonl"
METRICS = "metrics.json"

st.set_page_config(page_title="BTC 1H Forecast", page_icon="₿", layout="wide")


@st.cache_data(ttl=300)
def get_bars():
    return fetch_btc(limit=502).iloc[:-1].reset_index(drop=True)


def load_log():
    if not os.path.exists(LOG):
        return []
    rows = []
    with open(LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def save_log(rows):
    with open(LOG, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


st.title("BTC/USDT — Next Hour Forecast")
st.caption("GBM + Student-t · AlphaI × Polaris")

if os.path.exists(METRICS):
    m = json.load(open(METRICS))
    c1, c2, c3 = st.columns(3)
    c1.metric("Coverage (30d)", f"{m['coverage']:.1%}")
    c2.metric("Avg width", f"${m['avg_width']:,.0f}")
    c3.metric("Winkler", f"{m['winkler']:,.0f}")
    st.divider()
else:
    st.warning("Run backtest.py first to generate metrics.json")

df = get_bars()
closes = df["close"].values
price = float(closes[-1])
last_t = df["open_time"].iloc[-1]
next_t = last_t + pd.Timedelta(hours=1)

lo, hi = predict_range(closes[-500:])

a, b, c = st.columns(3)
a.metric("BTC now", f"${price:,.2f}")
b.metric("Lo (95%)", f"${lo:,.2f}")
c.metric("Hi (95%)", f"${hi:,.2f}")

st.info(f"Next hour: **${lo:,.2f} – ${hi:,.2f}**  ·  width ${hi-lo:,.0f}  ·  closes {next_t:%H:%M UTC}")

# chart
hist = df.tail(50)
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=hist["open_time"], y=hist["close"],
    mode="lines+markers", line=dict(color="#F7931A", width=2),
    marker=dict(size=3), name="BTC",
))
fig.add_trace(go.Scatter(
    x=[last_t, next_t, next_t, last_t],
    y=[price, hi, lo, price],
    fill="toself", fillcolor="rgba(96,165,250,0.18)",
    line=dict(color="rgba(96,165,250,0.5)", width=1),
    name="95% range",
))
fig.add_hline(y=lo, line_dash="dot", line_color="#60A5FA")
fig.add_hline(y=hi, line_dash="dot", line_color="#34D399")
fig.update_layout(
    height=420, hovermode="x unified",
    xaxis_title="Time (UTC)", yaxis_title="Price",
    legend=dict(orientation="h", y=1.02),
    margin=dict(t=40),
)
st.plotly_chart(fig, use_container_width=True)

# Part C — persistent log
log = load_log()
dirty = False

# back-fill actuals for closed bars
have = {row["open_time"].isoformat(): float(row["close"]) for _, row in df.iterrows()}
for e in log:
    if e.get("actual") is None and e["next_bar_time"] in have:
        e["actual"] = have[e["next_bar_time"]]
        dirty = True

key = next_t.isoformat()
if not any(e["next_bar_time"] == key for e in log):
    log.append({
        "predicted_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "next_bar_time": key,
        "lo": round(lo, 2),
        "hi": round(hi, 2),
        "actual": None,
    })
    dirty = True

if dirty:
    save_log(log)

if any(e.get("actual") is not None for e in log):
    st.subheader("History")
    rows = []
    for e in reversed(log[-30:]):
        y = e.get("actual")
        hit = "—" if y is None else ("✓" if e["lo"] <= y <= e["hi"] else "✗")
        rows.append({
            "Bar": e["next_bar_time"][:16].replace("T", " "),
            "Lo": f"${e['lo']:,.0f}",
            "Hi": f"${e['hi']:,.0f}",
            "Actual": f"${y:,.0f}" if y is not None else "—",
            "Hit": hit,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
left, right = st.columns([4, 1])
left.caption(f"Updated {pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M UTC}")
if right.button("Refresh"):
    st.cache_data.clear()
    st.rerun()
