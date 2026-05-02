import requests
import pandas as pd

_BINANCE = "https://api.binance.com/api/v3/klines"
_BYBIT   = "https://api.bybit.com/v5/market/kline"


def fetch_btc(limit=1000, end_time=None):
    """Try Binance; fall back to Bybit on 451 (US geo-block on Render)."""
    try:
        return _binance(limit, end_time)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 451:
            return _bybit(limit)
        raise


def _binance(limit, end_time=None):
    params = {"symbol": "BTCUSDT", "interval": "1h", "limit": min(limit, 1000)}
    if end_time is not None:
        params["endTime"] = end_time

    r = requests.get(_BINANCE, params=params, timeout=15)
    r.raise_for_status()

    cols = ["open_time", "open", "high", "low", "close", "volume",
            "close_time", "qv", "trades", "tb", "tq", "_"]
    df = pd.DataFrame(r.json(), columns=cols)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)
    return df.sort_values("open_time").reset_index(drop=True)


def _bybit(limit=1000):
    # Bybit returns newest-first; max 1000 per call
    params = {
        "category": "spot",
        "symbol":   "BTCUSDT",
        "interval": "60",
        "limit":    min(limit, 1000),
    }
    r = requests.get(_BYBIT, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("retCode", 0) != 0:
        raise RuntimeError(f"Bybit error: {data.get('retMsg')}")

    # list columns: [startTime(ms), open, high, low, close, volume, turnover]
    rows = data["result"]["list"]
    df = pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume", "turnover"])
    df["open_time"] = pd.to_datetime(df["open_time"].astype(int), unit="ms", utc=True)
    df["close_time"] = df["open_time"] + pd.Timedelta(hours=1) - pd.Timedelta(milliseconds=1)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)

    return df.sort_values("open_time").reset_index(drop=True)
