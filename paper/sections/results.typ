= Results <sec:results>

== Replication baseline (AQR QMJ-Canada)
Loading the public AQR Quality Minus Junk series for Canada, our
replication spans 1989-07 to 2026-03 (441 monthly observations). The
headline statistics are an annualized excess return of $8.6%$, annualized
volatility of $13.4%$, and a Sharpe ratio of $0.64$. The maximum drawdown
is $-37.0%$. A Carhart-style four-factor regression against the AQR
Canadian market, size, value, and momentum series yields a monthly alpha
of $0.70%$ ($t = 4.46$), or roughly $8.8%$ annualised, with loadings of
$beta_"MKT" = -0.26$, $beta_"SMB" = -0.39$, $beta_"HML" = +0.02$,
$beta_"UMD" = +0.11$ and $R^2 = 0.30$. The Sharpe falls within $0.30$ of
the $0.65$ figure reported in AFP 2019 Table II for Canada, satisfying
our replication gate.

=== External cross-check: Ken French Developed FF5+UMD
To validate the replication against a separate factor library, we
regress AQR QMJ-Canada on Ken French's Developed-region five-factor
panel @ff2015 augmented with the Developed momentum factor (1990-11 to
2026-03, 425 overlapping months). The alpha remains positive and
significant at $0.52%$/month ($t = 3.00$, $approx 6.4%$ annualised),
shrinking relative to the AQR-Canadian regression because the FF5
panel includes operating profitability (RMW). The QMJ-CAN series loads
strongly and significantly on RMW ($beta = +0.61$, $t = 4.16$) — the
predicted alignment between the Quality construct and a direct
profitability factor. The market and size loadings retain the same
sign and rough magnitude ($beta_"Mkt-RF" = -0.23$, $beta_"SMB" = -0.35$),
HML turns marginally positive ($beta = +0.29$, $t = 1.91$), CMA is
insignificant, and momentum is small and insignificant. Overall the
cross-check both _confirms_ the alpha and _validates_ the construct.

== paper-Q on TSX small/mid-caps
We then form a long–short paper-Q tercile portfolio on a 109-ticker TSX
small/mid-cap universe over 2011-12 to 2025-11 (168 months). With value
weighting (dollar-volume proxy), the gross annualised return is $+1.0%$
against $30.6%$ volatility (Sharpe $0.03$); the equal-weight variant is
sharply negative (Sharpe $-0.33$) and highly volatile, reflecting a few
microcap blow-ups. Average monthly leg turnover is $7.4%$.

#figure(
  image("../figures/cumret.pdf", width: 95%),
  caption: [Cumulative growth of \$1 invested in the paper-Q long–short
  (VW tercile) on TSX small/mid-caps vs the AQR QMJ-Canada factor over
  the common sample.],
) <fig:cumret>

== Calibration of paper-Q against AQR QMJ-Canada
The key diagnostic for our extension is whether paper-Q captures the same
underlying construct as the fundamentals-based AQR Quality factor.
Regressing the paper-Q long–short return on AQR QMJ-Canada yields
$hat(beta) = -0.08$ ($t = -0.38$) with $R^2 approx 0$ and a
contemporaneous correlation of $-0.03$. Our _a priori_ calibration gate
(Spearman $rho gt.eq 0.3$) is *not met*. A Carhart-CAN regression of the
same series produces an insignificant alpha ($t = 0.26$), a marginal
negative $"SMB"$ loading ($beta = -0.48$, $t = -1.89$), and an
insignificant negative momentum loading.

== Interpretation
The price-derived proxy, in this universe, is essentially uncorrelated
with fundamentals-based Quality. We interpret this as a falsification of
the hypothesis that the AQR QMJ premium can be recovered from
price/return statistics alone in a commodity- and resource-heavy
small-cap universe. The result is consistent with several plausible
mechanisms: (i) in a market dominated by junior energy and mining
issuers, low-volatility names are disproportionately defensive sectors
whose risk is structurally distinct from the operational quality QMJ
targets; (ii) the Safety leg of QMJ depends on accounting inputs whose
price proxies are contaminated by sectoral exposure; (iii) yfinance
survivorship effects on the universe likely bias the result toward names
that recovered, blunting any defensive premium.

== A regime shift around COVID
A subperiod split reveals that the full-sample null masks two
qualitatively different regimes. From 2011-12 through February 2020 the
VW-tercile paper-Q L/S earned an annualised $+14.3%$ at $30.4%$
volatility (net Sharpe $+0.47$). From March 2020 onward the same
construction returned $-18.1%$ annualised (net Sharpe $-0.60$). The flip
coincides with the energy and base-metals rally of 2020–2022 in which
the highest-volatility names within the universe led, mechanically
penalising a Safety-tilted long-short. The full Phase 5 cell sweep is
reported in @sec:robustness.
