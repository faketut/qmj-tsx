# QMJ on TSX Small-Caps

Replicating Asness, Frazzini, and Pedersen's *Quality Minus Junk* (RFS 2019) on Canadian
equities and extending it with a **price-derived Quality proxy** ("paper-Q") deployed on
TSX small-caps where free-source fundamentals are too thin for the original construction.

> *Working paper:* extends Asness QMJ to TSX small-caps; long-short portfolio results,
> robustness, and reproducible Python pipeline.

## Status

Work in progress. See `/memories/session/plan.md` for the full plan and verification gates.

## Quickstart

Requires Python ≥ 3.11 and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone <repo-url> qmj-tsx
cd qmj-tsx
uv sync
make all          # data → signals → backtest → paper PDF
```

Target wall-clock for a clean clone: ≤ 30 min on a modern laptop.

## CLI

```bash
qmj --help
qmj data prices                   # Phase 1 — yfinance monthly parquets
qmj data benchmarks               # Phase 1 — AQR QMJ/BAB-Canada
qmj data ken-french               # Phase 1 — Ken French Developed FF5 + UMD
qmj replicate                     # Phase 2 — AQR QMJ-Canada baseline + FF5-DEV cross-check
qmj signals paper-q               # Phase 3 — price-based Quality panel
qmj backtest                      # Phase 4 — long–short portfolio + summary stats
qmj robust                        # Phase 5 — weighting×buckets×subperiod×cost sweep,
                                   #   plus sector-exclusion and per-component horse race
qmj figure cumret                 # cumulative-return figure (paper-Q vs QMJ-CAN)
```

## Repo layout

```
src/qmj_tsx/
  data/        ingest, universe construction, AQR + Ken French loaders
  signals/     paper-Q (price-based) Quality components
  portfolio/   sort/weight/rebalance engine
  stats/       Newey-West regressions, replication baseline, robustness sweeps
  plots/       figure generators
paper/         Typst source (main.typ, sections/, tables/, figures/, references.bib)
tests/         unit + invariant tests (20 currently)
configs/       default.yaml — sample window, filters, cost assumptions
data/          raw/, interim/, processed/ (raw caches gitignored)
```

## Reproduction

| Target          | Produces                                                       |
| --------------- | -------------------------------------------------------------- |
| `make data`     | Cached parquets: prices, AQR benchmarks, Ken French FF5+UMD    |
| `make signals`  | paper-Q monthly panel                                          |
| `make backtest` | Long–short returns + summary                                   |
| `make robust`   | Headline sweep, sector-exclusion, per-component horse race     |
| `make figures`  | `paper/figures/cumret.pdf`                                     |
| `make paper`    | `paper/main.pdf` (via [Typst](https://typst.app))              |
| `make all`      | All of the above                                               |
| `make test`     | Run unit + invariant tests                                     |

## Data sources

All free, no subscriptions required:
- **Prices** — Yahoo Finance via `yfinance` (`.TO`, `.V` suffixes)
- **AQR factor series** — [AQR Datasets](https://www.aqr.com/Insights/Datasets) (QMJ + BAB Equity monthly, all countries)
- **Fama–French factors** — [Ken French data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) (Developed 5-factor + Developed momentum, monthly)

## License

MIT. See [LICENSE](LICENSE).
