= Data <sec:data>

All inputs are free and re-downloadable. We snapshot every source under
`data/raw/` and emit a manifest with SHA-256 hashes so the pipeline is
bit-reproducible from a fresh clone.

== AQR factor library
We pull the public monthly Quality Minus Junk and Betting Against Beta
workbooks @afp2019 @fp2014, plus AQR's Canadian market, SMB, HML, UMD,
and risk-free series. The QMJ-Canada sheet spans 1989-07 to 2026-03
(441 monthly observations) and serves as both the replication target
and the calibration benchmark for paper-Q.

== Equity prices and universe
Monthly adjusted-close prices and dollar volumes come from `yfinance`
for a hand-curated 115-ticker TSX small/mid-cap universe spanning the
ten GICS sectors. Of the 115 listed tickers, 109 had usable monthly
history over our 2010–2025 sample window after delisting and ingest
filters. We compute monthly simple returns from adjusted close,
normalising all timestamps to month-end (`yfinance` returns a mixture
of month-start and month-end indices across vintages, which we
harmonise at ingest).

== Sample window
The paper-Q signal requires at minimum a 60-month rolling beta
estimate, so the live backtest begins in 2011-12 and runs through
2025-11 (168 monthly observations).

== Benchmarks and risk-free rate
We use AQR's Canadian risk-free series throughout, both for the QMJ
replication regressions and for excess-return calculations on the
paper-Q long–short. For an external (non-AQR) cross-check of the
replication, we additionally pull Ken French's Developed-region
five-factor series @ff2015 plus the Developed momentum factor from
the Ken French data library. The downloader caches both CSVs under
`data/raw/ken_french/` and falls back to `curl` when the local Python
`ssl` module cannot validate the upstream certificate chain.

== Survivorship caveat
Our universe is sourced from a present-day TSX listing rather than a
point-in-time membership file. Firms that delisted before the snapshot
was taken are absent. This biases our results toward survivors, which,
if anything, _strengthens_ the case for a positive paper-Q premium. The
observed null result is therefore a conservative test.
