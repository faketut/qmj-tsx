"""Phase 5 — robustness sweep: weighting x buckets x subperiod x cost."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import Config
from ..data.ingest import assemble_price_panel, monthly_returns
from ..data.universe import load_smallcap_universe
from ..portfolio.construct import build_long_short, summarize


@dataclass(frozen=True)
class Subperiod:
    name: str
    start: str | None
    end: str | None

    def slice(self, s: pd.Series) -> pd.Series:
        start = pd.Timestamp(self.start) if self.start else s.index.min()
        end = pd.Timestamp(self.end) if self.end else s.index.max()
        return s.loc[(s.index >= start) & (s.index <= end)]


DEFAULT_SUBPERIODS = [
    Subperiod("full", None, None),
    Subperiod("pre-COVID", None, "2020-02-29"),
    Subperiod("post-COVID", "2020-03-01", None),
]


def run_robustness(cfg: Config) -> pd.DataFrame:
    """Sweep weighting × n_buckets × subperiod × cost; return one row per cell."""
    signal_path = cfg.data_processed / "paper_q_panel.parquet"
    if not signal_path.exists():
        raise FileNotFoundError(f"Run `qmj signals paper-q` first; missing {signal_path}")
    signal = pd.read_parquet(signal_path)
    prices = monthly_returns(assemble_price_panel(cfg.data_raw / "prices"))

    weightings = ["value", "equal"]
    bucket_grid = [3, 5]
    cost_grid = [0.0, 10.0, 25.0]

    rows: list[dict] = []
    for w in weightings:
        for nb in bucket_grid:
            bt = build_long_short(
                signal,
                prices,
                n_buckets=nb,
                long_bucket=nb,
                short_bucket=1,
                weighting=w,
                cost_bps=10.0,  # gross series independent of this; we re-cost below
            )
            gross = bt["ls_ret"]
            avg_to = float(bt["turnover"].mean())
            for sub in DEFAULT_SUBPERIODS:
                slc = sub.slice(gross)
                for c in cost_grid:
                    net = slc - bt["turnover"].reindex(slc.index).fillna(0.0) * (c / 10_000.0)
                    s_gross = summarize(slc)
                    s_net = summarize(net)
                    rows.append({
                        "weighting": w,
                        "n_buckets": nb,
                        "subperiod": sub.name,
                        "cost_bps": c,
                        "n_months": s_gross["n"],
                        "ann_ret_gross": s_gross["ann_ret"],
                        "ann_vol": s_gross["ann_vol"],
                        "sharpe_gross": s_gross["sharpe"],
                        "ann_ret_net": s_net["ann_ret"],
                        "sharpe_net": s_net["sharpe"],
                        "avg_turnover": avg_to,
                    })
    return pd.DataFrame(rows)


def to_typst(df: pd.DataFrame) -> str:
    """Compact Typst table — one row per (weighting, n_buckets, subperiod),
    columns by transaction cost. Wrapped in a `#figure(table(...))` block."""
    pivot = df.pivot_table(
        index=["weighting", "n_buckets", "subperiod", "n_months", "ann_vol", "avg_turnover"],
        columns="cost_bps",
        values="sharpe_net",
    ).reset_index()
    cost_cols = [c for c in pivot.columns if isinstance(c, float)]
    pivot = pivot.sort_values(["weighting", "n_buckets", "subperiod"])

    n_cols = 6 + len(cost_cols)
    header = (
        "[*Weighting*], [*Buckets*], [*Subperiod*], [*N*], [*Ann. vol*], "
        "[*Avg TO*], "
        + ", ".join(f"[*{int(c)} bps*]" for c in cost_cols)
    )

    body_rows: list[str] = []
    for _, r in pivot.iterrows():
        cells = [
            f"[{r['weighting']}]",
            f"[{int(r['n_buckets'])}]",
            f"[{r['subperiod']}]",
            f"[{int(r['n_months'])}]",
            f"[{r['ann_vol']:.1%}]",
            f"[{r['avg_turnover']:.1%}]",
        ]
        for c in cost_cols:
            v = r[c]
            cells.append("[--]" if pd.isna(v) else f"[{v:+.2f}]")
        body_rows.append(", ".join(cells))

    table_body = ",\n  ".join([header] + body_rows)
    return (
        "#figure(\n"
        f"  table(\n    columns: {n_cols},\n    align: (left, center, left, right, right, right, "
        + ", ".join(["right"] * len(cost_cols)) + "),\n  "
        f"  {table_body},\n  ),\n"
        '  caption: [Net Sharpe ratios for the paper-Q long–short across '
        'weighting, bucket count, subperiod, and round-trip cost.],\n'
        ") <tab:robustness>\n"
    )


def write_outputs(df: pd.DataFrame, cfg: Config) -> tuple[Path, Path]:
    out_dir = cfg.data_processed
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet = out_dir / "robustness.parquet"
    typ = cfg.root / "paper" / "tables" / "robustness.typ"
    typ.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet)
    typ.write_text(to_typst(df))
    return parquet, typ


# ---------------------------------------------------------------------------
# Phase 5.1 — sector exclusion (ex-resources) cut
# ---------------------------------------------------------------------------

DEFAULT_EXCLUDED_SECTORS: tuple[str, ...] = ("Energy", "Materials")


def run_sector_exclusion(
    cfg: Config,
    exclude_sectors: tuple[str, ...] = DEFAULT_EXCLUDED_SECTORS,
    cost_bps: float = 10.0,
) -> pd.DataFrame:
    """Re-run the headline VW tercile after dropping resource-sector tickers,
    compared side-by-side with the full universe across the three subperiods."""
    signal_path = cfg.data_processed / "paper_q_panel.parquet"
    if not signal_path.exists():
        raise FileNotFoundError(f"Run `qmj signals paper-q` first; missing {signal_path}")
    signal = pd.read_parquet(signal_path)
    prices = monthly_returns(assemble_price_panel(cfg.data_raw / "prices"))

    csv_rel = cfg.get("universe", "csv")
    if not csv_rel:
        raise RuntimeError("universe.csv must be configured for the sector-exclusion sweep")
    uni = load_smallcap_universe(cfg.resolve(csv_rel))
    excluded = set(uni.loc[uni["sector"].isin(exclude_sectors), "ticker"])
    excl_label = "Ex " + " & ".join(exclude_sectors)

    rows: list[dict] = []
    for label, drop in (("All sectors", set()), (excl_label, excluded)):
        sig = signal[~signal["ticker"].isin(drop)] if drop else signal
        n_kept = sig["ticker"].nunique()
        bt = build_long_short(
            sig, prices,
            n_buckets=3, long_bucket=3, short_bucket=1,
            weighting="value", cost_bps=cost_bps,
        )
        gross = bt["ls_ret"]
        turnover = bt["turnover"]
        for sub in DEFAULT_SUBPERIODS:
            slc = sub.slice(gross)
            net = slc - turnover.reindex(slc.index).fillna(0.0) * (cost_bps / 10_000.0)
            s_gross = summarize(slc)
            s_net = summarize(net)
            rows.append({
                "universe": label,
                "n_tickers": int(n_kept),
                "subperiod": sub.name,
                "n_months": int(s_gross["n"]),
                "ann_vol": float(s_gross["ann_vol"]),
                "ann_ret_net": float(s_net["ann_ret"]),
                "sharpe_net": float(s_net["sharpe"]),
            })
    return pd.DataFrame(rows)


def sector_exclusion_to_typst(
    df: pd.DataFrame,
    exclude_sectors: tuple[str, ...] = DEFAULT_EXCLUDED_SECTORS,
    cost_bps: float = 10.0,
) -> str:
    """Compact 6-row Typst table: universe x subperiod, net Sharpe at `cost_bps`."""
    df = df.sort_values(["universe", "subperiod"]).reset_index(drop=True)
    header = (
        "[*Universe*], [*Tickers*], [*Subperiod*], [*N*], "
        "[*Ann. vol*], [*Ann. ret (net)*], [*Net Sharpe*]"
    )
    body: list[str] = []
    for _, r in df.iterrows():
        body.append(", ".join([
            f"[{r['universe']}]",
            f"[{int(r['n_tickers'])}]",
            f"[{r['subperiod']}]",
            f"[{int(r['n_months'])}]",
            f"[{r['ann_vol']:.1%}]",
            f"[{r['ann_ret_net']:+.1%}]",
            f"[{r['sharpe_net']:+.2f}]",
        ]))
    table_body = ",\n  ".join([header] + body)
    excl_text = " and ".join(exclude_sectors)
    return (
        "#figure(\n"
        "  table(\n    columns: 7,\n"
        "    align: (left, right, left, right, right, right, right),\n  "
        f"  {table_body},\n  ),\n"
        f"  caption: [Headline paper-Q long\u2013short (VW tercile, 10 bps round-trip) "
        f"on the full TSX small/mid-cap universe vs the same construction after "
        f"dropping {excl_text} sector names. The post-COVID Sharpe gap isolates the "
        f"contribution of resource-sector exposure to the regime flip.],\n"
        ") <tab:sector-exclusion>\n"
    )


def write_sector_exclusion_outputs(
    df: pd.DataFrame,
    cfg: Config,
    exclude_sectors: tuple[str, ...] = DEFAULT_EXCLUDED_SECTORS,
) -> tuple[Path, Path]:
    out_dir = cfg.data_processed
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet = out_dir / "sector_exclusion.parquet"
    typ = cfg.root / "paper" / "tables" / "sector_exclusion.typ"
    typ.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet)
    typ.write_text(sector_exclusion_to_typst(df, exclude_sectors=exclude_sectors))
    return parquet, typ


# ---------------------------------------------------------------------------
# Phase 5.2 — per-component horse race
# ---------------------------------------------------------------------------

_COMPONENT_LABELS = {
    "z_idio_vol": "Idio. vol (−)",
    "z_beta": "Beta (−)",
    "z_max_drawdown": "Max DD (−)",
    "z_rolling_sharpe": "Rolling Sharpe (+)",
    "z_downside_semi_dev": "Downside semi-dev (−)",
    "paper_q": "paper-Q (composite)",
}


def run_component_horserace(cfg: Config, cost_bps: float = 10.0) -> pd.DataFrame:
    """Standalone VW tercile L/S for each paper-Q component plus the composite,
    reported across the three subperiods at the headline cost."""
    signal_path = cfg.data_processed / "paper_q_panel.parquet"
    if not signal_path.exists():
        raise FileNotFoundError(f"Run `qmj signals paper-q` first; missing {signal_path}")
    full = pd.read_parquet(signal_path)
    prices = monthly_returns(assemble_price_panel(cfg.data_raw / "prices"))

    component_cols = [c for c in full.columns if c.startswith("z_")] + ["paper_q"]

    rows: list[dict] = []
    for col in component_cols:
        sig = full[["date", "ticker", col]].rename(columns={col: "paper_q"}).dropna()
        if sig.empty:
            continue
        bt = build_long_short(
            sig, prices,
            n_buckets=3, long_bucket=3, short_bucket=1,
            weighting="value", cost_bps=cost_bps,
        )
        gross = bt["ls_ret"]
        turnover = bt["turnover"]
        for sub in DEFAULT_SUBPERIODS:
            slc = sub.slice(gross)
            net = slc - turnover.reindex(slc.index).fillna(0.0) * (cost_bps / 10_000.0)
            s_gross = summarize(slc)
            s_net = summarize(net)
            rows.append({
                "component": col,
                "label": _COMPONENT_LABELS.get(col, col),
                "subperiod": sub.name,
                "n_months": int(s_gross["n"]),
                "ann_vol": float(s_gross["ann_vol"]),
                "ann_ret_net": float(s_net["ann_ret"]),
                "sharpe_net": float(s_net["sharpe"]),
            })
    return pd.DataFrame(rows)


def component_horserace_to_typst(df: pd.DataFrame, cost_bps: float = 10.0) -> str:
    """One row per component; columns: full / pre-COVID / post-COVID net Sharpe."""
    pivot = df.pivot_table(
        index=["component", "label"],
        columns="subperiod",
        values="sharpe_net",
    ).reset_index()
    # Preserve definition order, composite last.
    order = list(_COMPONENT_LABELS.keys())
    pivot["__o"] = pivot["component"].map({c: i for i, c in enumerate(order)})
    pivot = pivot.sort_values("__o").drop(columns="__o")

    sub_order = ["full", "pre-COVID", "post-COVID"]
    header = "[*Component*], " + ", ".join(f"[*{s} Sharpe*]" for s in sub_order)

    body: list[str] = []
    for _, r in pivot.iterrows():
        cells = [f"[{r['label']}]"]
        for s in sub_order:
            v = r.get(s, float("nan"))
            cells.append("[--]" if pd.isna(v) else f"[{v:+.2f}]")
        body.append(", ".join(cells))

    table_body = ",\n  ".join([header] + body)
    return (
        "#figure(\n"
        "  table(\n    columns: 4,\n"
        "    align: (left, right, right, right),\n  "
        f"  {table_body},\n  ),\n"
        f"  caption: [Net Sharpe ratios (VW tercile L/S, {int(cost_bps)} bps round-trip) "
        f"for each paper-Q component used as a standalone signal, across the three "
        f"subperiods. Signs in parentheses indicate the sign-alignment applied so that "
        f"\"long the top tercile\" corresponds to higher quality.],\n"
        ") <tab:horserace>\n"
    )


def write_component_horserace_outputs(df: pd.DataFrame, cfg: Config) -> tuple[Path, Path]:
    out_dir = cfg.data_processed
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet = out_dir / "component_horserace.parquet"
    typ = cfg.root / "paper" / "tables" / "component_horserace.typ"
    typ.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet)
    typ.write_text(component_horserace_to_typst(df))
    return parquet, typ


# ---------------------------------------------------------------------------
# Phase 5.3 — orthogonalised paper-Q (PCA of components)
# ---------------------------------------------------------------------------

def _pca_loadings(
    panel: pd.DataFrame,
    component_cols: list[str],
    n_components: int = 2,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Run PCA on the stacked (date, ticker) × component matrix via SVD.

    Returns ``(scores, loadings, explained_var_ratio)`` where ``scores`` is a
    long-form DataFrame with columns ``[date, ticker, pc_1, pc_2, ...]`` and
    ``loadings`` is an ``(n_features, n_components)`` matrix aligned to
    ``component_cols``.
    """
    sub = panel[["date", "ticker"] + component_cols].dropna().copy()
    X = sub[component_cols].to_numpy()
    # The z-scored panel is roughly centred per-date already, but centre once
    # more globally to be safe before SVD.
    X = X - X.mean(axis=0, keepdims=True)
    # Economy SVD.
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    loadings = Vt[:n_components].T  # (n_features, n_components)
    scores = X @ loadings            # (n_obs, n_components)
    var_total = float((S ** 2).sum())
    explained = (S[:n_components] ** 2) / var_total
    out = sub[["date", "ticker"]].copy()
    for k in range(n_components):
        out[f"pc_{k + 1}"] = scores[:, k]
    return out, loadings, explained


def _align_pc_sign(loadings: np.ndarray, component_cols: list[str]) -> np.ndarray:
    """Flip sign of each PC so its mean loading on the four
    volatility-flavoured components (everything except rolling Sharpe) is
    *positive* — i.e. higher PC means "more defensive / safer", matching the
    paper-Q convention of higher = better quality."""
    vol_idx = [i for i, c in enumerate(component_cols) if c != "z_rolling_sharpe"]
    signs = np.ones(loadings.shape[1])
    for k in range(loadings.shape[1]):
        mean_vol_loading = float(loadings[vol_idx, k].mean())
        if mean_vol_loading < 0:
            signs[k] = -1.0
    return signs


def run_pca_signals(cfg: Config, cost_bps: float = 10.0, n_components: int = 2) -> tuple[pd.DataFrame, dict]:
    """Construct PC1, PC2, and a 2-PC composite signal; horse-race each as a
    standalone VW tercile L/S across the three subperiods.

    Returns ``(rows_df, meta)`` where ``meta`` carries the PCA loadings and
    explained-variance shares for inclusion in the paper.
    """
    signal_path = cfg.data_processed / "paper_q_panel.parquet"
    if not signal_path.exists():
        raise FileNotFoundError(f"Run `qmj signals paper-q` first; missing {signal_path}")
    full = pd.read_parquet(signal_path)
    component_cols = [c for c in full.columns if c.startswith("z_")]
    if not component_cols:
        raise RuntimeError("No z_* columns in paper-Q panel — cannot run PCA.")

    scores, loadings, explained = _pca_loadings(full, component_cols, n_components=n_components)
    signs = _align_pc_sign(loadings, component_cols)
    loadings = loadings * signs  # broadcast over n_components
    for k in range(n_components):
        scores[f"pc_{k + 1}"] = scores[f"pc_{k + 1}"] * signs[k]

    # Composite = mean of the (sign-aligned) PCs.
    pc_cols = [f"pc_{k + 1}" for k in range(n_components)]
    scores["pc_composite"] = scores[pc_cols].mean(axis=1)

    prices = monthly_returns(assemble_price_panel(cfg.data_raw / "prices"))

    rows: list[dict] = []
    signal_labels = [(c, f"PC{i+1}") for i, c in enumerate(pc_cols)] + [("pc_composite", "PC composite")]
    for col, label in signal_labels:
        sig = scores[["date", "ticker", col]].rename(columns={col: "paper_q"}).dropna()
        bt = build_long_short(
            sig, prices,
            n_buckets=3, long_bucket=3, short_bucket=1,
            weighting="value", cost_bps=cost_bps,
        )
        gross = bt["ls_ret"]
        turnover = bt["turnover"]
        for sub in DEFAULT_SUBPERIODS:
            slc = sub.slice(gross)
            net = slc - turnover.reindex(slc.index).fillna(0.0) * (cost_bps / 10_000.0)
            s_gross = summarize(slc)
            s_net = summarize(net)
            rows.append({
                "signal": col,
                "label": label,
                "subperiod": sub.name,
                "n_months": int(s_gross["n"]),
                "ann_vol": float(s_gross["ann_vol"]),
                "ann_ret_net": float(s_net["ann_ret"]),
                "sharpe_net": float(s_net["sharpe"]),
            })

    meta = {
        "component_cols": component_cols,
        "loadings": loadings,             # (n_features, n_components), sign-aligned
        "explained_var_ratio": explained, # length n_components
    }
    return pd.DataFrame(rows), meta


def pca_signals_to_typst(df: pd.DataFrame, meta: dict, cost_bps: float = 10.0) -> str:
    """Two stacked Typst tables: (i) PCA loadings + variance share,
    (ii) net Sharpe of PC1/PC2/composite across subperiods."""
    component_cols = meta["component_cols"]
    loadings = meta["loadings"]
    explained = meta["explained_var_ratio"]

    pretty = {
        "z_idio_vol": "Idio. vol (−)",
        "z_beta": "Beta (−)",
        "z_max_drawdown": "Max DD (−)",
        "z_rolling_sharpe": "Rolling Sharpe (+)",
        "z_downside_semi_dev": "Downside semi-dev (−)",
    }

    n_pc = loadings.shape[1]
    pc_headers = [f"PC{i+1} ({explained[i]:.0%})" for i in range(n_pc)]

    # --- loadings table ---
    head_a = "[*Component*], " + ", ".join(f"[*{h}*]" for h in pc_headers)
    rows_a = []
    for i, c in enumerate(component_cols):
        cells = [f"[{pretty.get(c, c)}]"]
        for k in range(n_pc):
            cells.append(f"[{loadings[i, k]:+.2f}]")
        rows_a.append(", ".join(cells))
    body_a = ",\n  ".join([head_a] + rows_a)
    cols_a = 1 + n_pc
    aligns_a = "left, " + ", ".join(["right"] * n_pc)

    table_loadings = (
        "#figure(\n"
        f"  table(\n    columns: {cols_a},\n"
        f"    align: ({aligns_a}),\n  "
        f"  {body_a},\n  ),\n"
        "  caption: [Sign-aligned principal-component loadings on the five "
        "z-scored paper-Q components, with cumulative variance share in "
        "parentheses. PC1 corresponds to the dominant volatility direction; "
        "PC2 picks up the rolling-Sharpe contrast.],\n"
        ") <tab:pca-loadings>\n"
    )

    # --- horse race table ---
    pivot = df.pivot_table(index=["signal", "label"], columns="subperiod", values="sharpe_net").reset_index()
    order = ["pc_1", "pc_2", "pc_composite"]
    pivot["__o"] = pivot["signal"].map({c: i for i, c in enumerate(order)})
    pivot = pivot.sort_values("__o").drop(columns="__o")
    sub_order = ["full", "pre-COVID", "post-COVID"]
    head_b = "[*Signal*], " + ", ".join(f"[*{s} Sharpe*]" for s in sub_order)
    rows_b = []
    for _, r in pivot.iterrows():
        cells = [f"[{r['label']}]"]
        for s in sub_order:
            v = r.get(s, float("nan"))
            cells.append("[--]" if pd.isna(v) else f"[{v:+.2f}]")
        rows_b.append(", ".join(cells))
    body_b = ",\n  ".join([head_b] + rows_b)

    table_sharpe = (
        "#figure(\n"
        "  table(\n    columns: 4,\n"
        "    align: (left, right, right, right),\n  "
        f"  {body_b},\n  ),\n"
        f"  caption: [Net Sharpe ratios (VW tercile L/S, {int(cost_bps)} bps round-trip) "
        f"for the PCA-orthogonalised paper-Q signals across the three subperiods. "
        f"PC1 and PC2 are orthogonal by construction; the composite is their mean.],\n"
        ") <tab:pca-sharpe>\n"
    )

    return table_loadings + "\n" + table_sharpe


def write_pca_outputs(df: pd.DataFrame, meta: dict, cfg: Config) -> tuple[Path, Path]:
    out_dir = cfg.data_processed
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet = out_dir / "pca_signals.parquet"
    typ = cfg.root / "paper" / "tables" / "pca_signals.typ"
    typ.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(parquet)
    typ.write_text(pca_signals_to_typst(df, meta))
    return parquet, typ
