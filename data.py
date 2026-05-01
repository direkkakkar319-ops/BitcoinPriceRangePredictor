import requests
import pandas as pd

KLINES_URL = "https://api.binance.com/api/v3/klines"


def fetch_btc(limit=1000, end_time=None):
    params = {"symbol": "BTCUSDT", "interval": "1h", "limit": limit}
    if end_time is not None:
        params["endTime"] = end_time

    r = requests.get(KLINES_URL, params=params, timeout=15)
    r.raise_for_status()

    cols = ["open_time", "open", "high", "low", "close", "volume",
            "close_time", "qv", "trades", "tb", "tq", "_"]
    df = pd.DataFrame(r.json(), columns=cols)

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)

    return df.sort_values("open_time").reset_index(drop=True)
