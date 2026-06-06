= Introduction <sec:intro>

The Quality Minus Junk (QMJ) factor of @afp2019 is one of the most
thoroughly documented anomalies of the past decade: high-quality firms
— those that are profitable, growing, safe, and well-managed — earn
persistently higher risk-adjusted returns than low-quality firms across
24 developed markets. AQR publishes monthly QMJ returns by country,
including for Canada, which makes the headline result independently
verifiable for any researcher with a spreadsheet. It does *not* make
the factor _deployable_ on Canadian small-caps: the construction
requires accounting fundamentals (gross profitability, accruals,
leverage, payout ratios) that are not free at the level of coverage
and point-in-time fidelity AFP use.

This paper has two contributions, both designed around full
reproducibility from free data.

+ *Replication.* We verify the AQR QMJ-Canada series end-to-end against
  the published series, report headline statistics, and estimate a
  Carhart-style four-factor regression using AQR's Canadian market,
  size, value, and momentum series. The Sharpe ratio falls within our
  pre-registered tolerance of the figure reported in AFP 2019 Table II,
  and the four-factor alpha is large and significant. As an external
  cross-check, we re-estimate the regression against the Ken French
  Developed five-factor model @ff2015 plus the Developed momentum
  series: the alpha survives and the series loads strongly on Robust
  Minus Weak (RMW), the predicted alignment between QMJ and a direct
  profitability factor.

+ *Price-based extension (paper-Q).* We construct a fundamentals-free
  quality proxy from five price- and return-derived components
  (idiosyncratic volatility, market beta, maximum drawdown, rolling
  Sharpe, downside semi-deviation), sign-aligned to AFP's Safety leg,
  cross-sectionally z-scored, and equal-weight composited. We deploy
  it as a monthly tercile long–short on a hand-curated 109-ticker TSX
  small/mid-cap universe and ask whether it recovers the AQR QMJ premium.

The answer is *no*, and the failure is informative in a specific way.
The contemporaneous correlation between paper-Q and AQR QMJ-Canada is
$-0.03$ over the common sample, and a Carhart-CAN regression of the
paper-Q long–short produces an insignificant alpha. A subperiod split
reveals a clean regime shift around COVID — net Sharpe $+0.47$ pre-2020,
$-0.60$ post-2020 — that two follow-up cuts sharpen further. Dropping
Energy and Materials tickers (the sectoral hypothesis) recovers only
about a third of the post-COVID damage, ruling out a pure resource-sector
story. A per-component horse race reveals the deeper mechanism: four of
the five paper-Q components (idio vol, beta, max drawdown, downside
semi-deviation) are essentially the same low-volatility signal in
different statistical clothing, and all four flip from clearly positive
pre-2020 to deeply negative post-2020. The fifth component, rolling
Sharpe, behaves qualitatively differently and is the lone survivor.
The composite's null is therefore *not* a generic failure of price
signals on TSX small-caps; it is the specific signature of a
post-pandemic low-volatility unwind, with rolling-Sharpe-style
momentum partially offsetting on the other side.

All code, intermediate data, and the Typst build pipeline for this
paper are public; the headline numbers regenerate from `make all` in
under a minute.
