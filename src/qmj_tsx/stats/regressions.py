"""OLS with Newey-West HAC standard errors."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass
class RegressionResult:
    params: pd.Series
    tvalues: pd.Series
    pvalues: pd.Series
    nobs: int
    r2: float

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {"coef": self.params, "t": self.tvalues, "p": self.pvalues}
        ).round(4)


def newey_west_ols(y: pd.Series, X: pd.DataFrame, lags: int = 6) -> RegressionResult:
    """Fit y ~ X with a constant and Newey-West HAC SEs at the given lag."""
    df = pd.concat([y.rename("__y__"), X], axis=1).dropna()
    if df.empty:
        raise ValueError("No overlapping observations between y and X.")
    Y = df["__y__"]
    Z = sm.add_constant(df.drop(columns="__y__"), has_constant="add")
    model = sm.OLS(Y, Z).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return RegressionResult(
        params=model.params.rename(index={"const": "alpha"}),
        tvalues=model.tvalues.rename(index={"const": "alpha"}),
        pvalues=model.pvalues.rename(index={"const": "alpha"}),
        nobs=int(model.nobs),
        r2=float(model.rsquared),
    )


def annualize_alpha(monthly_alpha: float) -> float:
    """Compound a monthly alpha to annual."""
    return float((1.0 + monthly_alpha) ** 12 - 1.0)


def summary_stats(returns: pd.Series, periods_per_year: int = 12) -> dict[str, float]:
    r = returns.dropna()
    mu = r.mean() * periods_per_year
    vol = r.std() * np.sqrt(periods_per_year)
    cum = (1.0 + r).cumprod()
    peak = cum.cummax()
    dd = (cum / peak - 1.0).min()
    return {
        "n_months": int(r.size),
        "ann_ret": float(mu),
        "ann_vol": float(vol),
        "sharpe": float(mu / vol) if vol > 0 else float("nan"),
        "max_drawdown": float(dd) if not np.isnan(dd) else float("nan"),
        "hit_rate": float((r > 0).mean()),
    }
