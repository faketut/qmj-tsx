= Conclusion <sec:conclusion>

We set out to do two things: verify QMJ-Canada from public AQR data,
and ask whether a fundamentals-free, price-derived analogue can recover
the premium on TSX small-caps. The first succeeds twice over — the
headline Sharpe and four-factor alpha sit comfortably within our
pre-registered tolerance of @afp2019 against the AQR Canadian factor
library, and the alpha survives an independent regression against the
Ken French Developed five-factor plus momentum panel @ff2015, with a
strongly significant positive loading on RMW that confirms the
Quality–profitability link.

The second fails cleanly, and the failure is sharp rather than diffuse.
The composite paper-Q is essentially uncorrelated with AQR QMJ-Canada,
robust to weighting, sort granularity, and transaction cost. A clean
regime flip around COVID — net Sharpe $+0.47$ pre-2020, $-0.60$
post-2020 — is what drives the full-sample null. Three targeted
diagnostics narrow the economic interpretation. An ex-Energy /
ex-Materials universe recovers only about a third of the post-COVID
damage; a per-component horse race shows that four of the five
paper-Q components are highly correlated low-volatility signals that
all turned over together, while the fifth (rolling Sharpe) survived;
and a PCA decomposition reduces the entire signal set to a single
pricing axis (PC1 explains $60%$ of cross-component variance and
inherits the regime flip cleanly), with the second principal component
showing no pricing content in any subperiod. The regime shift is,
specifically, a post-pandemic *low-volatility unwind* on TSX
small/mid-caps; it is not a generic failure of price signals in this
universe.

Two limitations qualify the negative result. First, the universe is a
present-day TSX listing rather than a point-in-time membership file;
survivorship bias works _against_ finding the null, so the result is
conservative. Second, we make no attempt to neutralise sector exposure
beyond the coarse Energy + Materials drop reported in @sec:robustness;
finer sectoral cuts, or factor-residualised returns, would be a
natural next step. The PCA decomposition reported in @sec:robustness
has already addressed the third limitation flagged in earlier drafts
(equal-weighting of near-collinear components) and shown that the
single-factor structure of paper-Q is binding, not merely an artefact
of equal weighting.

The broader takeaway is methodological: free-data reproductions of
published factor premia in small markets are useful precisely because
they are willing to fail. A negative composite with a clean
diagnostic battery — zero correlation with the published benchmark,
identifiable regime shift, only partial sectoral explanation, and a
clear single-component culprit — constrains the universe of admissible
economic stories far more sharply than a marginally positive headline
number would.
