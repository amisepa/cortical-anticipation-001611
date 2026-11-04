"""Pooling (metafor rma.mv via Rscript), TOST and Bayes factor (spec v0.3 Sections 6.5, 7)."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import integrate, stats

R_SCRIPT = Path(__file__).with_name("pool.R")
RSCRIPT = str(Path(__import__("sys").executable).with_name("Rscript"))


def pool(df: pd.DataFrame) -> pd.DataFrame:
    """df columns: rep, culture, experiment, yi, vi. One REML fit per rep (batched in one R call)."""
    with tempfile.TemporaryDirectory() as d:
        i, o = Path(d) / "in.csv", Path(d) / "out.csv"
        df[["rep", "culture", "experiment", "yi", "vi"]].to_csv(i, index=False)
        subprocess.run([RSCRIPT, str(R_SCRIPT), str(i), str(o)], check=True, capture_output=True)
        return pd.read_csv(o)


def tost(est: float, se: float, df: float, bound: float, alpha: float = 0.05) -> dict:
    """Equivalence shown if the (1 - 2 alpha) CI lies inside (-bound, bound)."""
    p_lo = 1 - stats.t.cdf((est + bound) / se, df)
    p_hi = stats.t.cdf((est - bound) / se, df)
    return dict(p_tost=float(max(p_lo, p_hi)), equivalent=bool(max(p_lo, p_hi) < alpha))


def bf10(est: float, se: float, scale: float) -> float:
    """BF10 with normal likelihood N(est | theta, se^2) and a Cauchy(0, scale) prior on theta (two-sided)."""
    like = lambda th: stats.norm.pdf(est, th, se) * stats.cauchy.pdf(th, 0, scale)  # noqa: E731
    lo, hi = est - 12 * se, est + 12 * se
    m1 = integrate.quad(like, -np.inf, lo, limit=200)[0] + integrate.quad(like, lo, hi, limit=200, points=[0.0, est])[0] \
        + integrate.quad(like, hi, np.inf, limit=200)[0]
    return float(m1 / stats.norm.pdf(est, 0, se))
