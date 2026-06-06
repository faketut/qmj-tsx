"""Tests for the cached TSX price parquets shipped with the repo."""

from __future__ import annotations

import pandas as pd
import pytest

from qmj_tsx.config import load_config
from qmj_tsx.data.ingest import assemble_price_panel, monthly_returns


@pytest.fixture(scope="module")
def panel():
    cfg = load_config()
    return assemble_price_panel(cfg.data_raw / "prices")


def test_panel_nonempty(panel):
    assert not panel.empty
    assert {"date", "ticker", "adj_close", "volume", "dollar_volume"} <= set(panel.columns)


def test_panel_dates_are_monthly(panel):
    # All cached series are monthly downloads.
    sample = panel[panel["ticker"] == panel["ticker"].iloc[0]].sort_values("date")
    gaps = sample["date"].diff().dropna().dt.days
    # Allow 28–35 day spacing (month-end variability).
    assert ((gaps >= 25) & (gaps <= 35)).mean() > 0.9


def test_monthly_returns_finite(panel):
    out = monthly_returns(panel)
    r = out["ret"].dropna()
    assert r.notna().sum() > 0
    assert (r.abs() < 1.0).mean() > 0.95  # no obviously corrupt observations
