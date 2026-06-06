"""AQR factor series loaders (QMJ, BAB).

The AQR monthly factor workbooks store wide panels with countries as columns.
The DATA region starts at row index 18 (zero-indexed) and the date column is
labelled ``DATE``. Country codes are 3-letter ISO (e.g. ``CAN``, ``USA``).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_HEADER_ROW = 18


def _load_aqr_sheet(path: Path, sheet: str, country: str) -> pd.Series:
    df = pd.read_excel(path, sheet_name=sheet, header=_HEADER_ROW)
    if "DATE" not in df.columns or country not in df.columns:
        raise KeyError(
            f"Expected 'DATE' and '{country}' columns in {path.name}:{sheet}; "
            f"got {list(df.columns)[:8]}"
        )
    out = df[["DATE", country]].dropna(subset=[country]).copy()
    out["DATE"] = pd.to_datetime(out["DATE"])
    series = out.set_index("DATE")[country].astype(float)
    series.index.name = "date"
    series.name = country
    # AQR dates are month-end already; normalize to PeriodIndex for joins.
    series.index = series.index + pd.offsets.MonthEnd(0)
    return series.sort_index()


def load_aqr_qmj(path: Path, country: str = "CAN") -> pd.Series:
    return _load_aqr_sheet(path, sheet="QMJ Factors", country=country)


def load_aqr_bab(path: Path, country: str = "CAN") -> pd.Series:
    return _load_aqr_sheet(path, sheet="BAB Factors", country=country)


def load_aqr_market_rf(path: Path, country: str = "CAN") -> pd.Series:
    """Country market excess return (MKT minus RF)."""
    return _load_aqr_sheet(path, sheet="MKT", country=country)


def load_aqr_smb(path: Path, country: str = "CAN") -> pd.Series:
    return _load_aqr_sheet(path, sheet="SMB", country=country)


def load_aqr_hml(path: Path, country: str = "CAN") -> pd.Series:
    return _load_aqr_sheet(path, sheet="HML FF", country=country)


def load_aqr_umd(path: Path, country: str = "CAN") -> pd.Series:
    return _load_aqr_sheet(path, sheet="UMD", country=country)


def load_aqr_rf(path: Path, country: str = "CAN") -> pd.Series:
    """Risk-free rate (per AQR's RF tab; same series across countries)."""
    return _load_aqr_sheet(path, sheet="RF", country=country)
