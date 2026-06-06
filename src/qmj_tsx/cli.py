"""Top-level Click CLI: `qmj ...`."""

from __future__ import annotations

from pathlib import Path

import click

from .config import load_config


@click.group()
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to YAML config (default: configs/default.yaml).",
)
@click.pass_context
def main(ctx: click.Context, config_path: Path | None) -> None:
    """QMJ-TSX command line."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_path)


# ---------- data ----------
@main.group()
def data() -> None:
    """Data acquisition commands."""


@data.command("prices")
@click.option("--seed-only", is_flag=True, help="Use only the small seed list (skip the bundled universe CSV).")
@click.pass_context
def data_prices(ctx: click.Context, seed_only: bool) -> None:
    """Download/refresh per-ticker price parquets for the configured universe."""
    from .data.prices import fetch_seed_prices
    from .data.universe import universe_tickers

    cfg = ctx.obj["config"]
    csv_rel = cfg.get("universe", "csv")
    tickers: list[str]
    if seed_only or not csv_rel:
        tickers = list(cfg.get("universe", "seed_tickers", default=[]))
    else:
        csv_path = cfg.resolve(csv_rel)
        if not csv_path.exists():
            click.echo(f"[warn] universe CSV not found at {csv_path}; falling back to seed_tickers")
            tickers = list(cfg.get("universe", "seed_tickers", default=[]))
        else:
            tickers = universe_tickers(csv_path)
            seeds = list(cfg.get("universe", "seed_tickers", default=[]))
            for s in seeds:
                if s not in tickers:
                    tickers.append(s)

    start = cfg.get("sample", "start")
    end = cfg.get("sample", "end")
    out_dir = cfg.data_raw / "prices"
    click.echo(f"Fetching {len(tickers)} tickers ({start} → {end}) into {out_dir}")
    out = fetch_seed_prices(tickers, start=start, end=end, out_dir=out_dir)
    click.echo(f"Wrote/refreshed {len(out)} ticker parquets")


@data.command("universe")
@click.pass_context
def data_universe(ctx: click.Context) -> None:
    """Print the active universe (ticker, sector) summary."""
    from .data.universe import load_smallcap_universe

    cfg = ctx.obj["config"]
    csv_rel = cfg.get("universe", "csv")
    if not csv_rel:
        click.echo("No universe.csv configured.")
        return
    path = cfg.resolve(csv_rel)
    df = load_smallcap_universe(path)
    click.echo(f"Universe: {len(df)} tickers from {path}")
    if "sector" in df.columns:
        click.echo(df["sector"].value_counts().to_string())


@data.command("benchmarks")
@click.pass_context
def data_benchmarks(ctx: click.Context) -> None:
    """Load AQR factor series and produce a tidy monthly parquet."""
    from .data.benchmarks import load_aqr_qmj, load_aqr_bab

    cfg = ctx.obj["config"]
    country = cfg.get("benchmarks", "aqr", "country", default="CAN")
    qmj_path = cfg.data_raw / "aqr" / cfg.get("benchmarks", "aqr", "qmj_xlsx")
    bab_path = cfg.data_raw / "aqr" / cfg.get("benchmarks", "aqr", "bab_xlsx")

    qmj = load_aqr_qmj(qmj_path, country=country)
    bab = load_aqr_bab(bab_path, country=country)

    out_dir = cfg.data_processed
    out_dir.mkdir(parents=True, exist_ok=True)
    qmj.to_frame("qmj").to_parquet(out_dir / "aqr_qmj.parquet")
    bab.to_frame("bab").to_parquet(out_dir / "aqr_bab.parquet")
    click.echo(f"AQR {country} QMJ: {len(qmj)} months  BAB: {len(bab)} months  -> {out_dir}")


@data.command("ken-french")
@click.pass_context
def data_ken_french(ctx: click.Context) -> None:
    """Cache the Ken French Developed 5-factor + momentum CSVs."""
    from .data.ken_french import load_ken_french_dev5, load_ken_french_dev_mom

    cfg = ctx.obj["config"]
    out_dir = cfg.data_raw / "ken_french"
    ff5 = load_ken_french_dev5(out_dir)
    mom = load_ken_french_dev_mom(out_dir)
    click.echo(
        f"Ken French Developed: FF5={ff5.shape[0]} months ({ff5.index.min():%Y-%m} → "
        f"{ff5.index.max():%Y-%m}), MOM={mom.shape[0]} months  -> {out_dir}"
    )


# ---------- replicate ----------
@main.command("replicate")
@click.pass_context
def replicate(ctx: click.Context) -> None:
    """Phase 2: AQR QMJ-Canada baseline stats + factor regression."""
    from .stats.replication import run_replication

    cfg = ctx.obj["config"]
    report = run_replication(cfg)
    click.echo(report)


# ---------- signals ----------
@main.group()
def signals() -> None:
    """Signal construction commands."""


@signals.command("paper-q")
@click.pass_context
def signals_paper_q(ctx: click.Context) -> None:
    """Compute monthly paper-Q panel from cached price parquets."""
    from .signals.paper_q import build_paper_q_panel

    cfg = ctx.obj["config"]
    panel = build_paper_q_panel(cfg)
    out = cfg.data_processed / "paper_q_panel.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(out)
    click.echo(f"paper-Q panel: shape={panel.shape} -> {out}")


# ---------- backtest ----------
@main.command("backtest")
@click.pass_context
def backtest(ctx: click.Context) -> None:
    """Phase 4: long-short portfolio on the paper-Q panel."""
    from .portfolio.construct import run_backtest

    cfg = ctx.obj["config"]
    report = run_backtest(cfg)
    click.echo(report)


# ---------- robustness ----------
@main.command("robust")
@click.pass_context
def robust(ctx: click.Context) -> None:
    """Phase 5: sweep weighting × buckets × subperiod × cost, plus the
    Phase 5.1 ex-resources sector cut. Writes parquets + Typst tables."""
    from .stats.robustness import (
        run_robustness,
        run_sector_exclusion,
        run_component_horserace,
        run_pca_signals,
        write_outputs,
        write_sector_exclusion_outputs,
        write_component_horserace_outputs,
        write_pca_outputs,
    )

    cfg = ctx.obj["config"]
    df = run_robustness(cfg)
    parquet, typ = write_outputs(df, cfg)
    click.echo(f"Robustness rows: {len(df)} → {parquet}")
    click.echo(f"Typst table     → {typ}")
    # Print a compact view to stdout
    view = df[df["cost_bps"] == 10.0][
        ["weighting", "n_buckets", "subperiod", "n_months",
         "ann_ret_gross", "ann_vol", "sharpe_net", "avg_turnover"]
    ]
    click.echo("\nNet Sharpe at 10 bps round-trip:")
    click.echo(view.to_string(index=False))

    # Phase 5.1 — sector exclusion
    sx = run_sector_exclusion(cfg)
    sx_parquet, sx_typ = write_sector_exclusion_outputs(sx, cfg)
    click.echo(f"\nSector-exclusion rows: {len(sx)} → {sx_parquet}")
    click.echo(f"Typst table            → {sx_typ}")
    click.echo("\nEx-resources cut (VW tercile, 10 bps):")
    click.echo(sx[["universe", "n_tickers", "subperiod", "n_months",
                   "ann_vol", "ann_ret_net", "sharpe_net"]].to_string(index=False))

    # Phase 5.2 — per-component horse race
    hr = run_component_horserace(cfg)
    hr_parquet, hr_typ = write_component_horserace_outputs(hr, cfg)
    click.echo(f"\nComponent horse-race rows: {len(hr)} → {hr_parquet}")
    click.echo(f"Typst table                → {hr_typ}")
    pivot = (
        hr.pivot_table(index="label", columns="subperiod", values="sharpe_net")
        .reindex(columns=["full", "pre-COVID", "post-COVID"])
        .round(2)
    )
    click.echo("\nComponent-level Net Sharpe (VW tercile, 10 bps):")
    click.echo(pivot.to_string())

    # Phase 5.3 — PCA-orthogonalised paper-Q
    pca_df, pca_meta = run_pca_signals(cfg)
    pca_parquet, pca_typ = write_pca_outputs(pca_df, pca_meta, cfg)
    click.echo(f"\nPCA signals rows: {len(pca_df)} → {pca_parquet}")
    click.echo(f"Typst table       → {pca_typ}")
    click.echo(
        "\nPCA explained-variance share: "
        + ", ".join(f"PC{i+1}={v:.1%}" for i, v in enumerate(pca_meta["explained_var_ratio"]))
    )
    pca_pivot = (
        pca_df.pivot_table(index="label", columns="subperiod", values="sharpe_net")
        .reindex(columns=["full", "pre-COVID", "post-COVID"])
        .round(2)
    )
    click.echo("\nPCA-orthogonalised paper-Q Net Sharpe (VW tercile, 10 bps):")
    click.echo(pca_pivot.to_string())


# ---------- figures ----------
@main.group()
def figure() -> None:
    """Generate paper figures."""


@figure.command("cumret")
@click.pass_context
def figure_cumret(ctx: click.Context) -> None:
    """Cumulative return chart: paper-Q L/S vs AQR QMJ-CAN."""
    from .plots.figures import cumulative_returns_figure

    cfg = ctx.obj["config"]
    out = cumulative_returns_figure(cfg)
    click.echo(f"Wrote {out}")


if __name__ == "__main__":  # pragma: no cover
    main()
