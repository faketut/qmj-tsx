"""Headline figures for the paper."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ..config import Config
from ..data import benchmarks as bm


def cumulative_returns_figure(cfg: Config, out_path: Path | None = None) -> Path:
    """Cumulative return chart: paper-Q L/S (VW) vs AQR QMJ-CAN over the
    common sample, both compounded to 1.0 at the start."""
    bt_path = cfg.data_processed / "backtest_returns.parquet"
    if not bt_path.exists():
        raise FileNotFoundError(f"Run `qmj backtest` first; missing {bt_path}")
    bt = pd.read_parquet(bt_path)
    bt.index = pd.to_datetime(bt.index) + pd.offsets.MonthEnd(0)

    aqr_dir = cfg.data_raw / "aqr"
    qmj = bm.load_aqr_qmj(
        aqr_dir / cfg.get("benchmarks", "aqr", "qmj_xlsx"),
        country=cfg.get("benchmarks", "aqr", "country", default="CAN"),
    )

    paper_q = bt["ls_ret"].rename("paper-Q L/S (VW tercile)")
    qmj = qmj.rename("AQR QMJ-CAN")

    joined = pd.concat([paper_q, qmj], axis=1).dropna()
    cum = (1.0 + joined).cumprod()

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    for col in cum.columns:
        ax.plot(cum.index, cum[col], label=col, linewidth=1.4)
    ax.axhline(1.0, color="grey", linewidth=0.6, linestyle=":")
    ax.set_ylabel("Cumulative growth of \\$1")
    ax.set_xlabel("Month")
    ax.set_title("paper-Q (TSX small/mid-cap) vs AQR QMJ-Canada")
    ax.legend(loc="best", frameon=False)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()

    if out_path is None:
        out_path = cfg.root / "paper" / "figures" / "cumret.pdf"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)
    return out_path
