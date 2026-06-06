"""yfinance price loader with parquet cache."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


def fetch_seed_prices(
    tickers: Iterable[str],
    start: str,
    end: str,
    out_dir: Path,
    interval: str = "1mo",
) -> list[Path]:
    """Download monthly prices for each ticker and write per-ticker parquet caches.

    Skips a ticker if the parquet already covers the requested end date.
    """
    import yfinance as yf

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    end_ts = pd.to_datetime(end)

    for ticker in tickers:
        path = out_dir / f"{ticker}.parquet"
        if path.exists():
            existing = pd.read_parquet(path)
            existing.index = pd.to_datetime(existing.index)
            if not existing.empty and existing.index.max() >= end_ts - pd.Timedelta(days=35):
                written.append(path)
                continue

        df = yf.download(
            ticker,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if df.empty:
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )
        df.index.name = "date"
        df.to_parquet(path)
        written.append(path)
    return written
