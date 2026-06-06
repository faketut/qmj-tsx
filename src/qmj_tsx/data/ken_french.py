"""Ken French Developed-region factor loaders.

Fetches and parses the monthly CSVs published on Ken French's data library.
Used for an external (non-AQR) cross-check of the Phase 2 replication.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import pandas as pd
import requests

_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
_DEV5_URL = _BASE + "Developed_5_Factors_CSV.zip"
_DEVMOM_URL = _BASE + "Developed_Mom_Factor_CSV.zip"

# Datasets are returned in percent; we divide by 100 to match AQR's decimal scale.
_PCT = 100.0


def _download_bytes(url: str) -> bytes:
    """Download a URL. Tries ``requests`` first; if Python's ssl rejects the
    corporate CA chain, falls back to ``curl --cacert $SSL_CERT_FILE``."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content
    except requests.exceptions.SSLError:
        if shutil.which("curl") is None:
            raise
        cmd = ["curl", "-sSfL"]
        ca = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
        if ca and Path(ca).exists():
            cmd += ["--cacert", ca]
        cmd.append(url)
        out = subprocess.run(cmd, check=True, capture_output=True)
        return out.stdout


def _fetch_zip_csv(url: str, out_dir: Path) -> Path:
    """Download a Ken French ZIP and cache the unpacked CSV under ``out_dir``.
    Returns the local CSV path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_name = url.rsplit("/", 1)[-1]
    csv_name = zip_name.replace("_CSV.zip", ".csv")
    csv_path = out_dir / csv_name
    if csv_path.exists():
        return csv_path
    blob = _download_bytes(url)
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        inner = next((n for n in zf.namelist() if n.lower().endswith(".csv")), None)
        if inner is None:
            raise RuntimeError(f"No CSV inside {zip_name}")
        csv_path.write_bytes(zf.read(inner))
    return csv_path


def _parse_monthly_block(csv_path: Path) -> pd.DataFrame:
    """Parse the monthly block (header line ending with the first data row whose
    label is YYYYMM, stopping at the first non-monthly row)."""
    text = csv_path.read_text(encoding="latin-1")
    lines = text.splitlines()
    # Find the first row whose first cell is a 6-digit YYYYMM.
    monthly_re = re.compile(r"^\s*(\d{6})\s*,")
    start = next((i for i, ln in enumerate(lines) if monthly_re.match(ln)), None)
    if start is None:
        raise RuntimeError(f"No monthly rows found in {csv_path}")
    # Header is the first non-blank line above `start` that contains commas.
    header_idx = next(
        i for i in range(start - 1, -1, -1)
        if "," in lines[i] and lines[i].strip()
    )
    # End: first row after `start` whose first cell is not YYYYMM.
    end = start
    while end < len(lines) and monthly_re.match(lines[end]):
        end += 1
    csv_block = "\n".join([lines[header_idx]] + lines[start:end])
    df = pd.read_csv(io.StringIO(csv_block))
    df.columns = [c.strip() for c in df.columns]
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col].astype(str), format="%Y%m")
    df = df.set_index(date_col)
    df.index = df.index + pd.offsets.MonthEnd(0)
    df.index.name = "date"
    return df.astype(float) / _PCT


def fetch_ken_french(cache_dir: Path) -> tuple[Path, Path]:
    """Download both Developed 5-Factor + Momentum CSVs into ``cache_dir``."""
    f5 = _fetch_zip_csv(_DEV5_URL, cache_dir)
    mom = _fetch_zip_csv(_DEVMOM_URL, cache_dir)
    return f5, mom


def load_ken_french_dev5(cache_dir: Path) -> pd.DataFrame:
    """Return monthly Developed 5-factor frame with columns
    ``[Mkt-RF, SMB, HML, RMW, CMA, RF]`` in decimal units."""
    f5, _ = fetch_ken_french(cache_dir)
    return _parse_monthly_block(f5)


def load_ken_french_dev_mom(cache_dir: Path) -> pd.Series:
    """Return the Developed momentum (WML) monthly series in decimal units."""
    _, mom = fetch_ken_french(cache_dir)
    df = _parse_monthly_block(mom)
    # The momentum file usually has a single column (``Mom`` or ``WML``).
    col = df.columns[0]
    return df[col].rename("WML")
