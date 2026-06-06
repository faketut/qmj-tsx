"""Smoke tests for the Phase 5 robustness sweep + headline figure."""

from __future__ import annotations

from pathlib import Path

import pytest

from qmj_tsx.config import load_config


@pytest.fixture(scope="module")
def cfg_with_signal():
    cfg = load_config()
    panel = cfg.data_processed / "paper_q_panel.parquet"
    if not panel.exists():
        pytest.skip("paper_q_panel.parquet absent — run `qmj signals paper-q` first.")
    return cfg


def test_robustness_runs(cfg_with_signal):
    from qmj_tsx.stats.robustness import run_robustness

    df = run_robustness(cfg_with_signal)
    assert {"weighting", "n_buckets", "subperiod", "cost_bps", "sharpe_net"} <= set(df.columns)
    assert len(df) == 2 * 2 * 3 * 3  # weightings × buckets × subperiods × costs
    assert df["n_months"].max() > 100


def test_cumret_figure_writes_pdf(cfg_with_signal, tmp_path: Path):
    from qmj_tsx.plots.figures import cumulative_returns_figure

    # backtest output must exist
    if not (cfg_with_signal.data_processed / "backtest_returns.parquet").exists():
        pytest.skip("backtest_returns.parquet absent — run `qmj backtest` first.")

    out = cumulative_returns_figure(cfg_with_signal, out_path=tmp_path / "cumret.pdf")
    assert out.exists()
    assert out.stat().st_size > 1024


def test_sector_exclusion_runs(cfg_with_signal):
    from qmj_tsx.stats.robustness import run_sector_exclusion, sector_exclusion_to_typst

    df = run_sector_exclusion(cfg_with_signal)
    # 2 universes × 3 subperiods
    assert len(df) == 6
    assert {"universe", "subperiod", "sharpe_net", "n_tickers"} <= set(df.columns)
    # Ex-resources cut should retain strictly fewer tickers than the full one
    full_n = df.loc[df["universe"] == "All sectors", "n_tickers"].iloc[0]
    ex_n = df.loc[df["universe"].str.startswith("Ex "), "n_tickers"].iloc[0]
    assert ex_n < full_n
    typ = sector_exclusion_to_typst(df)
    assert "tab:sector-exclusion" in typ
    assert "table(" in typ


def test_component_horserace_runs(cfg_with_signal):
    from qmj_tsx.stats.robustness import run_component_horserace, component_horserace_to_typst

    df = run_component_horserace(cfg_with_signal)
    # 6 components (5 z-scored + composite) × 3 subperiods
    assert len(df) == 18
    assert {"component", "label", "subperiod", "sharpe_net"} <= set(df.columns)
    assert df["component"].nunique() == 6
    typ = component_horserace_to_typst(df)
    assert "tab:horserace" in typ
    assert "Rolling Sharpe" in typ


def test_pca_signals_runs(cfg_with_signal):
    from qmj_tsx.stats.robustness import run_pca_signals, pca_signals_to_typst

    df, meta = run_pca_signals(cfg_with_signal, n_components=2)
    # 3 signals × 3 subperiods
    assert len(df) == 9
    assert df["signal"].nunique() == 3
    assert {"signal", "label", "subperiod", "sharpe_net"} <= set(df.columns)
    # Explained variance shares: positive and sum to <= 1, PC1 >= PC2.
    ev = meta["explained_var_ratio"]
    assert len(ev) == 2
    assert (ev > 0).all() and ev.sum() <= 1.0 + 1e-9
    assert ev[0] >= ev[1]
    typ = pca_signals_to_typst(df, meta)
    assert "tab:pca-loadings" in typ
    assert "tab:pca-sharpe" in typ
