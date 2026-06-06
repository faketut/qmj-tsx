"""Unit + invariant tests for the core pipeline math."""

from __future__ import annotations

import numpy as np
import pandas as pd

from qmj_tsx.portfolio.construct import assign_buckets, build_long_short
from qmj_tsx.signals.paper_q import _max_dd_from_log, _xs_zscore


def test_zscore_zero_mean_unit_var():
    df = pd.DataFrame([[1.0, 2.0, 3.0, 4.0, 5.0]])
    z = _xs_zscore(df)
    assert abs(z.iloc[0].mean()) < 1e-12
    assert abs(z.iloc[0].std() - 1.0) < 1e-12


def test_max_drawdown_hand_calc():
    # log returns: +0.1, -0.3, +0.1 → cumlog 0.1, -0.2, -0.1 → peak series 0.1, 0.1, 0.1
    # max drawdown = 0.1 - (-0.2) = 0.3
    arr = np.array([0.1, -0.3, 0.1])
    assert abs(_max_dd_from_log(arr) - 0.3) < 1e-12


def test_assign_buckets_partition():
    s = pd.Series(np.linspace(0, 1, 30))
    b = assign_buckets(s, 3)
    assert set(b.dropna().unique()) <= {1, 2, 3}
    counts = b.value_counts().sort_index()
    # Each tercile gets ~equal share.
    assert counts.min() >= 9


def test_long_short_three_stock_toy():
    """Hand-built panel: stock A always best, C always worst.
    Long-short should equal A_return - C_return for every period."""
    dates = pd.date_range("2020-01-31", periods=4, freq="ME")
    tickers = ["A", "B", "C"]
    sig_rows = []
    price_rows = []
    for d in dates:
        for t, score, r, dv in zip(
            tickers,
            [3.0, 2.0, 1.0],          # paper_q
            [0.05, 0.02, -0.03],      # this-month return
            [1_000_000, 1_000_000, 1_000_000],
        ):
            sig_rows.append({"date": d, "ticker": t, "paper_q": score})
            price_rows.append({
                "date": d, "ticker": t, "ret": r, "dollar_volume": dv,
            })
    signal_panel = pd.DataFrame(sig_rows)
    price_panel = pd.DataFrame(price_rows)

    bt = build_long_short(
        signal_panel, price_panel,
        n_buckets=3, long_bucket=3, short_bucket=1,
        weighting="equal", cost_bps=0.0,
    )
    # Position formed at t earns next month's return (A=0.05, C=-0.03).
    expected = 0.05 - (-0.03)
    realised = bt["ls_ret"].dropna()
    assert len(realised) >= 1
    assert (realised - expected).abs().max() < 1e-12
