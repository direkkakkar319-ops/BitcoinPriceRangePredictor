import requests
import pandas as pd

_BINANCE       = "https://api.binance.com/api/v3/klines"
_CRYPTOCOMPARE = "https://min-api.cryptocompare.com/data/v2/histohour"

# HTTP status codes that mean "this region is blocked"
_GEO_BLOCKED = {451, 403}


def fetch_btc(limit=1000, end_time=None):
    """Try Binance; fall back to CryptoCompare on geo-block (Render US servers)."""
    try:
        return _binance(limit, end_time)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code in _GEO_BLOCKED:
            return _cryptocompare(limit)
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


def _cryptocompare(limit=1000):
    # Returns limit+1 bars (includes the current open bar); we drop it like Binance
    params = {"fsym": "BTC", "tsym": "USD", "limit": min(limit, 2000)}
    r = requests.get(_CRYPTOCOMPARE, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("Response") != "Success":
        raise RuntimeError(f"CryptoCompare error: {data.get('Message')}")

    rows = data["Data"]["Data"]
    df = pd.DataFrame(rows)
    df["open_time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df["close_time"] = df["open_time"] + pd.Timedelta(hours=1) - pd.Timedelta(milliseconds=1)
    df = df.rename(columns={"volumefrom": "volume"})
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(float)

    return df.sort_values("open_time").reset_index(drop=True)
