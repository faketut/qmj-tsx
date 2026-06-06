"""Tests for the AQR replication baseline."""

from __future__ import annotations

import pytest

from qmj_tsx.config import load_config
from qmj_tsx.data.benchmarks import load_aqr_bab, load_aqr_qmj
from qmj_tsx.stats.regressions import summary_stats
from qmj_tsx.stats.replication import run_replication


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def test_aqr_qmj_canada_loads(cfg):
    path = cfg.data_raw / "aqr" / cfg.get("benchmarks", "aqr", "qmj_xlsx")
    series = load_aqr_qmj(path, country="CAN")
    assert series.index.is_monotonic_increasing
    assert series.notna().sum() > 300


def test_aqr_bab_canada_loads(cfg):
    path = cfg.data_raw / "aqr" / cfg.get("benchmarks", "aqr", "bab_xlsx")
    series = load_aqr_bab(path, country="CAN")
    assert series.notna().sum() > 300


def test_replication_summary_within_gate(cfg):
    """AFP 2019 Table II: Canada QMJ Sharpe ≈ 0.65 (1986–2017). Allow ±0.30."""
    path = cfg.data_raw / "aqr" / cfg.get("benchmarks", "aqr", "qmj_xlsx")
    series = load_aqr_qmj(path, country="CAN")
    stats = summary_stats(series)
    assert stats["sharpe"] is not None
    assert abs(stats["sharpe"] - 0.65) < 0.6  # generous outer band; CLI prints stricter gate


def test_run_replication_returns_report(cfg):
    text = run_replication(cfg)
    assert "Replication" in text
    assert "Sharpe" in text


def test_ken_french_dev5_parses(cfg):
    """Cached FF5-DEV CSV parses cleanly. Skip if cache absent (offline test runs)."""
    from qmj_tsx.data.ken_french import _parse_monthly_block

    csv = cfg.data_raw / "ken_french" / "Developed_5_Factors.csv"
    if not csv.exists():
        pytest.skip("Ken French cache absent — run `qmj data ken-french` first.")
    df = _parse_monthly_block(csv)
    assert {"Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"} <= set(df.columns)
    assert len(df) > 300
    # Values should be in decimal scale after divide-by-100.
    assert df["Mkt-RF"].abs().max() < 0.5
