"""Phase 2 — Replication baseline for AQR QMJ-Canada.

Reports headline stats on the AQR QMJ-Canada series and, when the matching
MKT/SMB/HML/UMD country panels are available, runs a Carhart-style regression.
"""

from __future__ import annotations

import pandas as pd

from ..config import Config
from ..data import benchmarks as bm
from .regressions import newey_west_ols, summary_stats


def _try_load_factor_panel(qmj_path, country: str) -> pd.DataFrame:
    """Best-effort load of MKT/SMB/HML/UMD for the country from the QMJ workbook.
    Missing sheets/columns are skipped silently."""
    out: dict[str, pd.Series] = {}
    loaders = {
        "MKT": bm.load_aqr_market_rf,
        "SMB": bm.load_aqr_smb,
        "HML": bm.load_aqr_hml,
        "UMD": bm.load_aqr_umd,
    }
    for name, fn in loaders.items():
        try:
            out[name] = fn(qmj_path, country=country)
        except Exception:  # noqa: BLE001 — robust to missing panels
            continue
    if not out:
        return pd.DataFrame()
    return pd.concat(out, axis=1).dropna(how="all")


def run_replication(cfg: Config) -> str:
    country = cfg.get("benchmarks", "aqr", "country", default="CAN")
    aqr_dir = cfg.data_raw / "aqr"
    qmj_path = aqr_dir / cfg.get("benchmarks", "aqr", "qmj_xlsx")
    bab_path = aqr_dir / cfg.get("benchmarks", "aqr", "bab_xlsx")
    nw_lags = int(cfg.get("stats", "newey_west_lags", default=6))

    qmj = bm.load_aqr_qmj(qmj_path, country=country).rename("QMJ")
    try:
        bab = bm.load_aqr_bab(bab_path, country=country).rename("BAB")
    except Exception:  # noqa: BLE001
        bab = pd.Series(dtype=float, name="BAB")

    factors = _try_load_factor_panel(qmj_path, country=country)

    stats = summary_stats(qmj)
    lines = [
        "=" * 60,
        f"Replication: AQR QMJ-{country}",
        "=" * 60,
        f"Sample          : {qmj.index.min():%Y-%m} → {qmj.index.max():%Y-%m}  ({stats['n_months']} months)",
        f"Ann. excess ret : {stats['ann_ret']:>7.2%}",
        f"Ann. vol        : {stats['ann_vol']:>7.2%}",
        f"Sharpe          : {stats['sharpe']:>7.2f}",
        f"Max drawdown    : {stats['max_drawdown']:>7.2%}",
        f"Hit rate (mo>0) : {stats['hit_rate']:>7.2%}",
    ]

    # Verification gate (AFP 2019 Table II Canada Sharpe ≈ 0.65, sample 1986-2017).
    target = 0.65
    ok = abs(stats["sharpe"] - target) <= 0.30
    lines.append(f"Gate (Sharpe within 0.30 of AFP {target:.2f}): {'PASS' if ok else 'WARN'}")

    if not factors.empty:
        lines += ["", "-" * 60, "Carhart-style regression (Newey-West, lag=" + str(nw_lags) + ")", "-" * 60]
        reg = newey_west_ols(qmj, factors, lags=nw_lags)
        lines.append(reg.to_frame().to_string())
        lines.append(f"R² = {reg.r2:.3f}   N = {reg.nobs}")
        ann_alpha = (1.0 + reg.params.get("alpha", 0.0)) ** 12 - 1.0
        lines.append(f"Annualized alpha ≈ {ann_alpha:.2%}")

    if not bab.empty:
        joined = pd.concat([qmj.rename("QMJ"), bab.rename("BAB")], axis=1).dropna()
        if len(joined) > 24:
            corr = joined.corr().iloc[0, 1]
            lines.append("")
            lines.append(f"corr(QMJ, BAB) over overlap ({len(joined)} mo): {corr:+.3f}")

    # ------------------------------------------------------------------
    # External cross-check: regress AQR QMJ-CAN on Ken French Developed
    # five-factor + momentum panel. This validates the replication
    # against a different factor library (FF5+UMD-DEV instead of AQR-CAN).
    # ------------------------------------------------------------------
    ff5_dir = cfg.data_raw / "ken_french"
    try:
        from ..data.ken_french import load_ken_french_dev5, load_ken_french_dev_mom

        ff5 = load_ken_french_dev5(ff5_dir).drop(columns=["RF"])
        mom = load_ken_french_dev_mom(ff5_dir)
        ff_panel = pd.concat([ff5, mom.rename("UMD")], axis=1).dropna()
    except Exception as exc:  # noqa: BLE001
        lines += ["", f"[ff5-dev cross-check skipped: {exc}]"]
    else:
        joined = pd.concat([qmj.rename("QMJ"), ff_panel], axis=1).dropna()
        if len(joined) < 24:
            lines += ["", "[ff5-dev cross-check skipped: insufficient overlap]"]
        else:
            lines += [
                "",
                "-" * 60,
                f"Ken French Developed FF5+UMD cross-check (Newey-West, lag={nw_lags})",
                "-" * 60,
                f"Overlap         : {joined.index.min():%Y-%m} → {joined.index.max():%Y-%m}  ({len(joined)} mo)",
            ]
            reg2 = newey_west_ols(joined["QMJ"], joined.drop(columns=["QMJ"]), lags=nw_lags)
            lines.append(reg2.to_frame().to_string())
            lines.append(f"R² = {reg2.r2:.3f}   N = {reg2.nobs}")
            ann_alpha2 = (1.0 + reg2.params.get("alpha", 0.0)) ** 12 - 1.0
            lines.append(f"Annualized alpha ≈ {ann_alpha2:.2%}")

    return "\n".join(lines)
