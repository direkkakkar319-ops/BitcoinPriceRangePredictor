import numpy as np
from scipy import stats


def predict_range(closes, n_sims=10_000, vol_window=72, conf=0.95, seed=None):
    closes = np.asarray(closes, dtype=float)
    rets = np.diff(np.log(closes))

    recent = rets[-vol_window:]
    recent = recent[np.isfinite(recent)]

    df, loc, scale = stats.t.fit(recent)
    df = float(np.clip(df, 2.1, 50))
    scale = max(float(scale), 1e-8)

    rng = np.random.default_rng(seed)
    sim = rng.standard_t(df, size=n_sims) * scale + loc
    prices = closes[-1] * np.exp(sim)

    a = 1 - conf
    lo, hi = np.percentile(prices, [100 * a / 2, 100 * (1 - a / 2)])
    return float(lo), float(hi)
