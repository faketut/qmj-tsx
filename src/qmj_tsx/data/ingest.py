"""Shared ingest helpers: parquet cache and panel assembly."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_price_parquet(path: Path) -> pd.DataFrame:
    """Read a single ticker price parquet and normalize the index to month-end."""
    df = pd.read_parquet(path)
    df.index = pd.to_datetime(df.index)
    df.index = df.index + pd.offsets.MonthEnd(0)
    df.index.name = "date"
    # Collapse any duplicate month-end timestamps that can arise when a series
    # contains both month-start and month-end observations (yfinance behaviour
    # for monthly downloads varies by ticker).
    df = df[~df.index.duplicated(keep="last")]
    return df.sort_index()


def assemble_price_panel(prices_dir: Path) -> pd.DataFrame:
    """Stack per-ticker parquets into a long panel: (date, ticker, adj_close, volume, dollar_volume)."""
    rows: list[pd.DataFrame] = []
    for p in sorted(prices_dir.glob("*.parquet")):
        ticker = p.stem
        df = read_price_parquet(p)
        if "adj_close" not in df.columns:
            continue
        out = pd.DataFrame(
            {
                "adj_close": df["adj_close"],
                "volume": df.get("volume", pd.Series(index=df.index, dtype=float)),
            }
        )
        out["dollar_volume"] = out["adj_close"] * out["volume"]
        out["ticker"] = ticker
        out = out.reset_index().rename(columns={"index": "date"})
        rows.append(out)
    if not rows:
        return pd.DataFrame(columns=["date", "ticker", "adj_close", "volume", "dollar_volume"])
    panel = pd.concat(rows, ignore_index=True)
    return panel[["date", "ticker", "adj_close", "volume", "dollar_volume"]].sort_values(
        ["date", "ticker"]
    )


def monthly_returns(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly log and simple returns from a long price panel."""
    panel = panel.sort_values(["ticker", "date"])
    panel["ret"] = panel.groupby("ticker")["adj_close"].pct_change()
    return panel
