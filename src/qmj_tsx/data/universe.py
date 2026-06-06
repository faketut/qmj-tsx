"""Universe assembly: TSX/TSXV ticker lists and size/liquidity filters."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_smallcap_universe(path: Path) -> pd.DataFrame:
    """Load the bundled TSX small/mid-cap CSV (ticker, sector).

    Lines starting with ``#`` are ignored; an empty ``sector`` is allowed.
    """
    df = pd.read_csv(path, comment="#")
    df["ticker"] = df["ticker"].str.strip()
    df = df[df["ticker"].astype(bool)].drop_duplicates("ticker").reset_index(drop=True)
    if "sector" in df.columns:
        df["sector"] = df["sector"].fillna("").str.strip()
    return df


def universe_tickers(path: Path) -> list[str]:
    return load_smallcap_universe(path)["ticker"].tolist()


def apply_liquidity_filter(
    panel: pd.DataFrame,
    min_dollar_vol: float,
    lookback_days: int = 63,
) -> pd.DataFrame:
    """Filter the panel to (date, ticker) rows whose trailing average dollar
    volume meets the threshold. Operates on a monthly panel; ``lookback_days``
    is converted to whole months (rounded up)."""
    months = max(1, round(lookback_days / 21))
    panel = panel.sort_values(["ticker", "date"]).copy()
    panel["avg_dv"] = (
        panel.groupby("ticker")["dollar_volume"]
        .rolling(months, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )
    return panel[panel["avg_dv"] >= min_dollar_vol].drop(columns=["avg_dv"])


def small_cap_bucket(
    panel: pd.DataFrame,
    market_cap_col: str = "market_cap",
    cutoff_pct: float = 0.30,
) -> pd.DataFrame:
    """Return rows belonging to the bottom ``cutoff_pct`` of market cap each month.
    If ``market_cap_col`` is absent, falls back to dollar_volume as a proxy."""
    if market_cap_col not in panel.columns:
        market_cap_col = "dollar_volume"
    panel = panel.copy()
    panel["_rank"] = panel.groupby("date")[market_cap_col].rank(pct=True, ascending=True)
    return panel[panel["_rank"] <= cutoff_pct].drop(columns=["_rank"])
