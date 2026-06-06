#figure(
  table(
    columns: 3,
    align: (left, right, right),
    [*Component*], [*PC1 (60%)*], [*PC2 (22%)*],
  [Idio. vol (−)], [+0.43], [+0.25],
  [Beta (−)], [+0.37], [+0.53],
  [Max DD (−)], [+0.55], [-0.10],
  [Rolling Sharpe (+)], [+0.27], [-0.80],
  [Downside semi-dev (−)], [+0.54], [-0.05],
  ),
  caption: [Sign-aligned principal-component loadings on the five z-scored paper-Q components, with cumulative variance share in parentheses. PC1 corresponds to the dominant volatility direction; PC2 picks up the rolling-Sharpe contrast.],
) <tab:pca-loadings>

#figure(
  table(
    columns: 4,
    align: (left, right, right, right),
    [*Signal*], [*full Sharpe*], [*pre-COVID Sharpe*], [*post-COVID Sharpe*],
  [PC1], [-0.23], [+0.34], [-0.85],
  [PC2], [-0.11], [-0.14], [-0.08],
  [PC composite], [-0.16], [+0.31], [-0.74],
  ),
  caption: [Net Sharpe ratios (VW tercile L/S, 10 bps round-trip) for the PCA-orthogonalised paper-Q signals across the three subperiods. PC1 and PC2 are orthogonal by construction; the composite is their mean.],
) <tab:pca-sharpe>
