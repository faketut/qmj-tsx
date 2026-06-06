"""Long-short bucket backtester operating on a (date, ticker, score) panel.

Conventions
-----------
* Signals are computed at month *t* close from data ≤ *t*.
* Portfolios are formed at *t* and held over month *t+1*.
* Returns are realised next-month adj-close-to-adj-close.
* Costs are charged on full notional turned over each rebalance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import Config
from ..data.ingest import assemble_price_panel, monthly_returns


def assign_buckets(scores: pd.Series, n_buckets: int) -> pd.Series:
    """Cross-sectional bucket assignment (1 = lowest, n_buckets = highest)."""
    if scores.dropna().empty:
        return pd.Series(index=scores.index, dtype="Int64")
    try:
        return pd.qcut(scores, n_buckets, labels=False, duplicates="drop") + 1
    except ValueError:
        return pd.Series(index=scores.index, dtype="Int64")


def build_long_short(
    signal_panel: pd.DataFrame,
    price_panel: pd.DataFrame,
    n_buckets: int = 3,
    long_bucket: int | None = None,
    short_bucket: int = 1,
    weighting: str = "value",
    cost_bps: float = 10.0,
) -> pd.DataFrame:
    """Form monthly long-short portfolios from a (date, ticker, paper_q) panel.

    Returns a DataFrame indexed by date with columns:
    ``long_ret``, ``short_ret``, ``ls_ret`` (long − short), ``ls_ret_net``
    (after one round-trip cost charged on turnover), and ``turnover``.
    """
    if long_bucket is None:
        long_bucket = n_buckets

    sig = signal_panel[["date", "ticker", "paper_q"]].dropna().copy()
    sig["bucket"] = sig.groupby("date")["paper_q"].transform(
        lambda s: assign_buckets(s, n_buckets)
    )

    # Next-month returns: ret at t+1 belongs to position formed at t.
    pr = price_panel.sort_values(["ticker", "date"]).copy()
    pr["next_ret"] = pr.groupby("ticker")["ret"].shift(-1)
    pr["mkt_cap_proxy"] = pr["dollar_volume"]  # proxy when true cap not available

    merged = sig.merge(
        pr[["date", "ticker", "next_ret", "mkt_cap_proxy"]],
        on=["date", "ticker"],
        how="inner",
    ).dropna(subset=["next_ret", "bucket"])

    def _weighted(sub: pd.DataFrame) -> float:
        if weighting == "equal" or sub["mkt_cap_proxy"].sum() <= 0:
            return float(sub["next_ret"].mean())
        w = sub["mkt_cap_proxy"] / sub["mkt_cap_proxy"].sum()
        return float((w * sub["next_ret"]).sum())

    long_side = (
        merged[merged["bucket"] == long_bucket]
        .groupby("date", group_keys=False)
        .apply(_weighted, include_groups=False)
    )
    short_side = (
        merged[merged["bucket"] == short_bucket]
        .groupby("date", group_keys=False)
        .apply(_weighted, include_groups=False)
    )

    out = pd.DataFrame({"long_ret": long_side, "short_ret": short_side}).dropna()
    out["ls_ret"] = out["long_ret"] - out["short_ret"]

    # Turnover: average across legs of (#new members) / (#members), per rebalance.
    def _leg_turnover(bucket_id: int) -> pd.Series:
        membership = (
            merged[merged["bucket"] == bucket_id]
            .assign(present=1)
            .pivot_table(index="date", columns="ticker", values="present", aggfunc="max")
            .fillna(0)
            .astype(int)
        )
        if membership.empty:
            return pd.Series(dtype=float)
        prev = membership.shift(1).fillna(0).astype(int)
        adds = ((membership == 1) & (prev == 0)).sum(axis=1)
        size = membership.sum(axis=1).replace(0, pd.NA)
        return (adds / size).astype(float)

    long_to = _leg_turnover(long_bucket)
    short_to = _leg_turnover(short_bucket)
    avg_to = pd.concat([long_to, short_to], axis=1).mean(axis=1)
    out["turnover"] = avg_to.reindex(out.index).fillna(0.0)

    out["ls_ret_net"] = out["ls_ret"] - out["turnover"] * (cost_bps / 10_000.0)
    out.index.name = "date"
    return out


# ---------------------------------------------------------------- CLI driver


def summarize(returns: pd.Series, periods_per_year: int = 12) -> dict[str, float]:
    r = returns.dropna()
    if r.empty:
        return {"n": 0, "ann_ret": float("nan"), "ann_vol": float("nan"), "sharpe": float("nan")}
    mu = r.mean() * periods_per_year
    vol = r.std() * np.sqrt(periods_per_year)
    return {
        "n": int(r.size),
        "ann_ret": float(mu),
        "ann_vol": float(vol),
        "sharpe": float(mu / vol) if vol > 0 else float("nan"),
    }


def run_backtest(cfg: Config) -> str:
    from ..signals.paper_q import build_paper_q_panel

    panel_path = cfg.data_processed / "paper_q_panel.parquet"
    if panel_path.exists():
        signal_panel = pd.read_parquet(panel_path)
    else:
        signal_panel = build_paper_q_panel(cfg)

    prices = assemble_price_panel(cfg.data_raw / "prices")
    prices = monthly_returns(prices)

    bt = build_long_short(
        signal_panel,
        prices,
        n_buckets=int(cfg.get("portfolio", "n_buckets", default=3)),
        long_bucket=int(cfg.get("portfolio", "long_bucket", default=3)),
        short_bucket=int(cfg.get("portfolio", "short_bucket", default=1)),
        weighting=str(cfg.get("portfolio", "weighting", default="value")),
        cost_bps=float(cfg.get("portfolio", "costs_bps_round_trip", default=10)),
    )

    out_path = cfg.data_processed / "backtest_returns.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bt.to_parquet(out_path)

    gross = summarize(bt["ls_ret"])
    net = summarize(bt["ls_ret_net"])
    lines = [
        "=" * 60,
        "paper-Q long-short backtest",
        "=" * 60,
        f"Sample          : {bt.index.min():%Y-%m} → {bt.index.max():%Y-%m}  ({gross['n']} months)",
        f"Gross ann. ret  : {gross['ann_ret']:>7.2%}",
        f"Gross ann. vol  : {gross['ann_vol']:>7.2%}",
        f"Gross Sharpe    : {gross['sharpe']:>7.2f}",
        f"Net (costs)     : ann_ret={net['ann_ret']:.2%}  Sharpe={net['sharpe']:.2f}",
        f"Avg turnover    : {bt['turnover'].mean():>7.2%}",
        f"Output          : {out_path}",
    ]
    return "\n".join(lines)
