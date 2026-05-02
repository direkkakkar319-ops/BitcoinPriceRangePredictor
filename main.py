import json
import os
import threading
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data import fetch_btc
from model import predict_range

ROOT = Path(__file__).parent
LOG = ROOT / "predictions_log.jsonl"
METRICS = ROOT / "metrics.json"

app = FastAPI(title="BTC 1H Forecaster")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_lock = threading.Lock()
_cache = {"t": None, "df": None}


def get_bars():
    now = pd.Timestamp.now(tz="UTC")
    if _cache["df"] is not None and (now - _cache["t"]).total_seconds() < 60:
        return _cache["df"]
    df = fetch_btc(limit=502).iloc[:-1].reset_index(drop=True)
    _cache["t"] = now
    _cache["df"] = df
    return df


def read_log():
    if not LOG.exists():
        return []
    with open(LOG) as f:
        return [json.loads(l) for l in f if l.strip()]


def write_log(rows):
    with open(LOG, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


@app.get("/api/state")
def state():
    df = get_bars()
    closes = df["close"].values
    price = float(closes[-1])
    last_t = df["open_time"].iloc[-1]
    next_t = last_t + pd.Timedelta(hours=1)

    lo, hi = predict_range(closes[-500:])
    lo, hi = round(lo, 2), round(hi, 2)

    with _lock:
        log = read_log()
        have = {row["open_time"].isoformat(): float(row["close"])
                for _, row in df.iterrows()}
        for e in log:
            if e.get("actual") is None and e["next_bar_time"] in have:
                e["actual"] = round(have[e["next_bar_time"]], 2)

        key = next_t.isoformat()
        if not any(e["next_bar_time"] == key for e in log):
            log.append({
                "predicted_at": pd.Timestamp.now(tz="UTC").isoformat(),
                "next_bar_time": key,
                "lo": lo,
                "hi": hi,
                "actual": None,
            })

        write_log(log)
        history = list(reversed(log[-100:]))

    metrics = json.load(open(METRICS)) if METRICS.exists() else None

    bars = df.tail(50)[["open_time", "open", "high", "low", "close"]].copy()
    bars["open_time"] = bars["open_time"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    bars = bars.to_dict(orient="records")

    return {
        "current_price": price,
        "lo": lo,
        "hi": hi,
        "last_bar_time": last_t.isoformat(),
        "next_bar_time": next_t.isoformat(),
        "bars": bars,
        "metrics": metrics,
        "history": history,
    }


@app.get("/")
def root():
    return {"ok": True, "service": "btc-1h-forecaster"}
