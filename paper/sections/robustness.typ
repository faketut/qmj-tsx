= Robustness <sec:robustness>

== Headline sweep
@tab:robustness sweeps the headline paper-Q long–short over weighting
scheme (value vs equal), sort granularity (terciles vs quintiles),
subperiod (full sample, pre-COVID, post-COVID), and round-trip
transaction cost (0, 10, 25 bps). The qualitative picture is stable
across cells: paper-Q earns no meaningful premium on TSX small-caps
regardless of specification, and the equal-weight book is dominated by
microcap volatility.

#include "../tables/robustness.typ"

== Sector exclusion (ex-resources)
The conclusion in @sec:results conjectured that the COVID regime flip
was driven by Energy and Materials exposure — sectors in which the
defensive "low-volatility" leg of paper-Q maps onto a structurally
different risk than QMJ's Safety construct. @tab:sector-exclusion tests
this directly by re-running the headline VW tercile after dropping all
Energy and Materials names (76 of 109 tickers retained).

The result only partially supports the conjecture. Dropping resources
*compresses* the pre-COVID net Sharpe from $+0.47$ to $+0.10$ — most of
the pre-2020 alpha was in fact a resource-sector defensive play. The
post-COVID Sharpe rises from $-0.60$ to $-0.41$, a meaningful but
incomplete recovery. The full-sample number is essentially flat in
either cut. We read this as evidence that the sectoral story explains
about a third of the post-COVID damage; the remainder is a genuine
breakdown of the price-based proxy across the full cross-section,
consistent with a broader post-pandemic re-pricing of low-volatility
stocks (see the per-component decomposition below).

#include "../tables/sector_exclusion.typ"

== Per-component horse race
@tab:horserace decomposes the composite paper-Q into its five
z-scored components and runs each as a standalone VW tercile long–short
under the same 10 bps cost model. The pattern is sharp.

Four of the five components — idiosyncratic vol, beta, maximum
drawdown, and downside semi-deviation — are all variants of a single
underlying signal (the cross-section of price volatility). All four
post positive pre-COVID Sharpes ($+0.12$ to $+0.57$) and all four
collapse to comparable negative numbers post-COVID ($-0.53$ to $-0.92$).
The fifth component, rolling Sharpe, is the only price-momentum-flavoured
signal in the set and behaves qualitatively differently: it posts the
highest full-sample Sharpe ($+0.32$), the highest pre-COVID Sharpe
($+0.66$), and the shallowest post-COVID drawdown ($-0.10$).

Two conclusions follow. First, the composite's full-sample null result
is mechanically the average of one positive signal (rolling Sharpe)
and four highly correlated low-volatility siblings — equal-weighting
masks the heterogeneity. Second, the post-COVID regime shift documented
in @sec:results is _specifically a low-volatility unwind_: every
volatility-flavoured price signal in our set turned over together,
while the price-momentum component was comparatively unaffected. This
narrows the economic interpretation considerably and suggests that any
follow-up paper-Q construction should weight components by uniqueness
(e.g. PCA residuals) rather than equally.

#include "../tables/component_horserace.typ"

== PCA-orthogonalised paper-Q
The horse race motivates a more disciplined construction: rather than
equal-weighting five near-collinear components, project them onto an
orthogonal basis and price each axis separately. @tab:pca-loadings
shows the leading two principal components of the stacked
$("date" times "ticker")$ component matrix, sign-aligned so that
higher PC means "more defensive". The first principal component
explains $60%$ of cross-component variance and loads roughly uniformly
positive across all five components — a clean general-defensive axis.
The second explains a further $22%$ and is essentially a contrast
between rolling Sharpe ($-0.80$) and the beta-flavoured direction
($+0.53$), exactly the price-momentum-versus-low-volatility split the
horse race surfaced.

@tab:pca-sharpe runs each PC as a standalone VW tercile long–short
under the same 10 bps cost model. Three findings.

+ *PC1 reproduces the regime flip cleanly.* Pre-COVID Sharpe $+0.34$,
  post-COVID $-0.85$, full-sample $-0.23$. This is the dominant
  low-volatility direction and confirms that the post-pandemic break
  is in fact a one-factor phenomenon, not an artefact of
  equal-weighting correlated proxies.

+ *PC2 has no pricing content.* Its Sharpe is essentially zero in
  every subperiod (full $-0.11$, pre $-0.14$, post $-0.08$). The
  $+0.32$ full-sample Sharpe of standalone rolling Sharpe in
  @tab:horserace was in fact largely riding its positive correlation
  with the PC1 low-vol axis; once that correlation is purged the
  residual rolling-Sharpe contrast does not price.

+ *Equal-weighting PCs underperforms the unorthogonalised composite.*
  The two-PC composite Sharpe is $-0.16$ full-sample, worse than the
  $+0.03$ of the unweighted five-component paper-Q. This is the
  expected consequence of conclusions (1) and (2): averaging a
  pricing axis (PC1) with a non-pricing axis (PC2) dilutes signal.

The orthogonalisation thus does not _rescue_ paper-Q. What it does
is collapse the post-COVID regime story into a single dimension: the
TSX small/mid-cap low-volatility long–short broke in 2020 and has
not recovered.

#include "../tables/pca_signals.typ"
