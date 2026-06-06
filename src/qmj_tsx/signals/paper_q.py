"""paper-Q: a fundamentals-free Quality proxy built from price/return data only.

Components (all derivable from prices, sign-aligned so that **higher = better quality**):

* ``idio_vol``  : negative of 12-month idiosyncratic vol (residual from market-model)
* ``beta``      : negative of 60-month rolling beta vs the equal-weight market
* ``max_dd``    : negative of 36-month maximum drawdown magnitude (a positive number)
* ``sharpe``    : 24-month rolling Sharpe of monthly returns (annualized)
* ``downside``  : negative of 24-month downside semi-deviation

The composite paper-Q score for each (date, ticker) is the equal-weight mean of
cross-sectional z-scores of available components.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import Config
from ..data.ingest import assemble_price_panel, monthly_returns


# ---------------------------------------------------------------- component math


def _wide_returns(panel: pd.DataFrame) -> pd.DataFrame:
    """Pivot the long return panel to a wide (date x ticker) frame."""
    return panel.pivot(index="date", columns="ticker", values="ret").sort_index()


def _rolling_idio_vol(rets: pd.DataFrame, market: pd.Series, window: int) -> pd.DataFrame:
    """Idiosyncratic vol = std of the residual from a rolling market-model regression."""
    # For tractability: compute residual = r - beta_rolling * market, where
    # beta_rolling is the rolling cov / var. Then the std of that residual.
    market = market.reindex(rets.index)
    cov = rets.rolling(window).cov(market)
    var = market.rolling(window).var()
    beta = cov.div(var, axis=0)
    expected = beta.mul(market, axis=0)
    resid = rets - expected
    return resid.rolling(window).std()


def _rolling_beta(rets: pd.DataFrame, market: pd.Series, window: int) -> pd.DataFrame:
    market = market.reindex(rets.index)
    cov = rets.rolling(window).cov(market)
    var = market.rolling(window).var()
    return cov.div(var, axis=0)


def _rolling_max_drawdown(rets: pd.DataFrame, window: int) -> pd.DataFrame:
    """Largest peak-to-trough drawdown magnitude over the rolling window (>=0)."""
    log = np.log1p(rets.fillna(0.0))
    # Cumulative log return; drawdown vs trailing max.
    out = pd.DataFrame(np.nan, index=rets.index, columns=rets.columns)
    cum = log.rolling(window, min_periods=window).apply(_max_dd_from_log, raw=True)
    out.loc[:, :] = cum
    return out


def _max_dd_from_log(arr: np.ndarray) -> float:
    cum = np.cumsum(arr)
    peak = np.maximum.accumulate(cum)
    dd = peak - cum  # >=0
    return float(dd.max())


def _rolling_sharpe(rets: pd.DataFrame, window: int) -> pd.DataFrame:
    mu = rets.rolling(window).mean()
    sd = rets.rolling(window).std()
    return (mu / sd) * np.sqrt(12.0)


def _rolling_downside_semidev(rets: pd.DataFrame, window: int) -> pd.DataFrame:
    neg = rets.where(rets < 0, 0.0)
    return neg.rolling(window).std()


# ---------------------------------------------------------------- composite


def _xs_zscore(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional z-score along each row (date)."""
    mu = df.mean(axis=1)
    sd = df.std(axis=1).replace(0.0, np.nan)
    return df.sub(mu, axis=0).div(sd, axis=0)


def compute_components(panel: pd.DataFrame, cfg: Config) -> dict[str, pd.DataFrame]:
    """Return a dict of wide (date x ticker) component frames, sign-aligned."""
    rets = _wide_returns(panel)
    market = rets.mean(axis=1)  # equal-weight market proxy

    iv_w = int(cfg.get("signals", "paper_q", "idio_vol_window_months", default=12))
    b_w = int(cfg.get("signals", "paper_q", "beta_window_months", default=60))
    dd_w = int(cfg.get("signals", "paper_q", "drawdown_window_months", default=36))
    s_w = int(cfg.get("signals", "paper_q", "sharpe_window_months", default=24))

    return {
        "idio_vol": -_rolling_idio_vol(rets, market, iv_w),
        "beta": -_rolling_beta(rets, market, b_w),
        "max_drawdown": -_rolling_max_drawdown(rets, dd_w),
        "rolling_sharpe": _rolling_sharpe(rets, s_w),
        "downside_semi_dev": -_rolling_downside_semidev(rets, s_w),
    }


def build_paper_q_panel(cfg: Config) -> pd.DataFrame:
    """Assemble price panel → returns → components → composite paper-Q score.

    Returns a long-form DataFrame: columns = date, ticker, <each component z>, paper_q.
    """
    prices_dir = cfg.data_raw / "prices"
    panel = assemble_price_panel(prices_dir)
    if panel.empty:
        raise RuntimeError(f"No price parquets found under {prices_dir}")
    panel = monthly_returns(panel)

    enabled = cfg.get(
        "signals",
        "paper_q",
        "components",
        default=["idio_vol", "beta", "max_drawdown", "rolling_sharpe", "downside_semi_dev"],
    )
    comps = compute_components(panel, cfg)

    z_frames = {name: _xs_zscore(comps[name]) for name in enabled if name in comps}

    # Long-form melt then merge.
    long_pieces = []
    for name, z in z_frames.items():
        long_pieces.append(
            z.reset_index().melt(id_vars="date", var_name="ticker", value_name=f"z_{name}")
        )
    out = long_pieces[0]
    for piece in long_pieces[1:]:
        out = out.merge(piece, on=["date", "ticker"], how="outer")

    z_cols = [c for c in out.columns if c.startswith("z_")]
    out["paper_q"] = out[z_cols].mean(axis=1, skipna=True)
    return out.sort_values(["date", "ticker"]).reset_index(drop=True)
