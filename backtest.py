import json
import time
import numpy as np

from data import fetch_btc
from model import predict_range

N_TEST = 720
WARMUP = 200


def winkler(lo, hi, y, alpha=0.05):
    w = hi - lo
    if y < lo:
        return w + (2 / alpha) * (lo - y)
    if y > hi:
        return w + (2 / alpha) * (y - hi)
    return w


def evaluate(preds):
    hits, widths, scores = [], [], []
    for p in preds:
        lo, hi, y = p["lo"], p["hi"], p["actual"]
        hits.append(lo <= y <= hi)
        widths.append(hi - lo)
        scores.append(winkler(lo, hi, y))
    return {
        "coverage": float(np.mean(hits)),
        "avg_width": float(np.mean(widths)),
        "winkler": float(np.mean(scores)),
    }


def main():
    print(f"fetching {N_TEST + WARMUP + 10} bars...")
    df = fetch_btc(limit=N_TEST + WARMUP + 10).iloc[:-1].reset_index(drop=True)

    closes = df["close"].values
    times = df["open_time"]
    start = len(closes) - N_TEST

    preds = []
    t0 = time.perf_counter()
    for i in range(start, len(closes)):
        lo, hi = predict_range(closes[:i])
        preds.append({
            "open_time": times.iloc[i].isoformat(),
            "lo": round(lo, 2),
            "hi": round(hi, 2),
            "actual": round(float(closes[i]), 2),
        })
        n = i - start + 1
        if n % 100 == 0:
            print(f"  {n}/{N_TEST}  ({time.perf_counter()-t0:.1f}s)")

    m = evaluate(preds)
    print(f"\ncoverage: {m['coverage']:.4f}")
    print(f"width:    ${m['avg_width']:,.2f}")
    print(f"winkler:  {m['winkler']:,.2f}")

    with open("backtest_results.jsonl", "w") as f:
        for p in preds:
            f.write(json.dumps(p) + "\n")
    with open("metrics.json", "w") as f:
        json.dump(m, f, indent=2)


if __name__ == "__main__":
    main()
