# QMJ-TSX Blog Series

An eight-part companion series to the working paper
[*Quality Minus Junk on TSX Small-Caps: A Reproducible Replication and
Price-Based Extension*](https://github.com/faketut/qmj-tsx).

Each post is a standalone Markdown file with Jekyll-style YAML
frontmatter, ready to drop into the `_posts/` folder of a github.io
site. Filenames follow the Jekyll convention
`YYYY-MM-DD-slug.md`. If your site uses Hugo, the frontmatter is
also valid TOML-adjacent YAML; only `layout:` may need to be removed.

## Suggested reading order

**Research arc (the main story):**

1. [2026-06-06-qmj-tsx-null-result.md](2026-06-06-qmj-tsx-null-result.md) — When a famous anomaly refuses to travel.
2. [2026-06-13-low-vol-unwind-hiding-in-a-composite.md](2026-06-13-low-vol-unwind-hiding-in-a-composite.md) — Four signals, one factor, one regime break.
3. [2026-06-20-pca-as-diagnostic-not-rescue.md](2026-06-20-pca-as-diagnostic-not-rescue.md) — PCA can explain a strategy without saving it.

**Craft arc (how it was built):**

4. [2026-06-27-make-all-under-a-minute.md](2026-06-27-make-all-under-a-minute.md) — A reproducible quant paper in `make all`.
5. [2026-07-04-pre-registering-replication-gates.md](2026-07-04-pre-registering-replication-gates.md) — Pre-registering the gates that let you publish a null.
6. [2026-07-11-typst-instead-of-latex.md](2026-07-11-typst-instead-of-latex.md) — Why I wrote the paper in Typst.

**Data arc (what bit me):**

7. [2026-07-18-yfinance-survivorship-tsx.md](2026-07-18-yfinance-survivorship-tsx.md) — What yfinance survivorship does to a TSX small-cap backtest.
8. [2026-07-25-building-a-free-data-universe.md](2026-07-25-building-a-free-data-universe.md) — 109 tickers, three sources, zero subscriptions.

If you only read one: **post 2**. It is the most genuinely novel
finding and stands alone without requiring the reader to care about
QMJ specifically.
