= Methodology <sec:methodology>

== Replication target
QMJ in @afp2019 is the equal-weight composite of three legs —
Profitability, Growth, and Safety — minus their junk counterparts,
formed within size buckets. We take AQR's published Canadian series as
the ground truth and our replication consists of (i) loading the series
from the public workbook, (ii) recomputing the headline summary
statistics (annualised return, volatility, Sharpe, maximum drawdown),
and (iii) estimating a Carhart-CAN four-factor regression. We declare
the replication successful if our computed Sharpe falls within $0.30$
of the value reported in AFP 2019 Table II for Canada.

== paper-Q construction
The paper-Q score for stock $i$ in month $t$ is the equal-weight
composite of five cross-sectionally z-scored components, each derivable
from prices and returns alone:

#set enum(numbering: "(i)")
+ idiosyncratic volatility, 12-month rolling standard deviation of
  residuals from a single-factor market regression (sign $-$);
+ market beta, 60-month rolling OLS slope on the AQR Canadian market
  factor (sign $-$);
+ maximum drawdown over the trailing 36 months (sign $-$);
+ rolling Sharpe over the trailing 24 months (sign $+$);
+ downside semi-deviation, 12-month rolling standard deviation of
  negative returns (sign $-$).
#set enum(numbering: "1.")

Each component is winsorised at the cross-sectional 1st and 99th
percentiles before z-scoring. Sign alignment is chosen so that
_higher_ paper-Q corresponds to safer / higher-quality firms in the
spirit of AFP's Safety leg. The five z-scores are simple-averaged into
the composite `paper_q`.

== Portfolio formation
Each month we sort the cross-section of available names into terciles
on the prior month's `paper_q` and form a value-weighted long–short
portfolio (long the top tercile, short the bottom), using lagged
dollar volume as the value-weight proxy. The portfolio is rebalanced
monthly and held over the following month, eliminating look-ahead.
Transaction costs are modelled as a round-trip linear haircut applied
to monthly leg turnover, with headline results at 10 bps and a sweep
over ${0, 10, 25}$ bps reported in @sec:robustness.

== Inference
All point estimates are OLS; all standard errors are
Newey–West HAC @newey1987 with lag $L = 6$. Sharpe ratios are
annualised by $sqrt(12)$. Risk-adjusted alphas use AQR's Canadian
market, size, value, and momentum series for the headline
replication, and Ken French's Developed five-factor panel @ff2015
plus the Developed momentum series for the external cross-check
reported in @sec:results.
