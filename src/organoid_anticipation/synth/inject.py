"""Synthetic label-dependent signal for positive controls (spec 8.1).

`inject_counts` adds Poisson spikes so that, for trials with y == 1, the selected channels' expected
count is multiplied by (1 + delta). Counts for y == 0 trials are untouched.
"""
from __future__ import annotations

import numpy as np


def inject_counts(X: np.ndarray, y: np.ndarray, delta: float, channels: np.ndarray,
                  rng: np.random.Generator) -> np.ndarray:
    X = X.astype(float).copy()
    if delta <= 0 or len(channels) == 0:
        return X
    lam = X[:, channels].mean(axis=0) * delta  # per-channel added rate
    add = rng.poisson(lam[None, :], size=(int((y == 1).sum()), len(channels)))
    X[np.ix_(y == 1, channels)] += add
    return X


# ---------------------------------------------------------------- CP2 (D-063): shared by B2 power and the confirmatory run
TOP_K = 8   # "top-k" scenario: the k busiest included channels (label-free rate ranking); replaces "4 random channels"


def channel_subset(subset: str, incl: np.ndarray, pool: np.ndarray, W: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Channels for an injection scenario. 'all': every included channel; 'poolAB': included channels near a stimulation
    electrode; 'top8': the TOP_K included channels with the highest mean window count (label-free); 'ch4': 4 random
    included channels (superseded at CP2, kept for reference)."""
    idx = np.flatnonzero(incl)
    if subset == "all":
        return idx
    if subset == "poolAB":
        return idx[pool[idx] < 2]
    if subset == "top8":
        lam = W[:, 2:, :][..., idx].mean((0, 1))
        return idx[np.argsort(-lam, kind="stable")[:TOP_K]]
    if subset == "ch4":
        return rng.choice(idx, 4, replace=False)
    raise ValueError(subset)


def inject_multiplicative(W: np.ndarray, s: np.ndarray, chans: np.ndarray, delta: float, rng: np.random.Generator,
                          sessions, scenario: str = "both", ramp: bool = False) -> np.ndarray:
    """Copy of W (S, T, n_ch) with Poisson spikes added on `chans` so that a channel's expected window count is
    lambda_c * (1 + d)^(s1 + s2) ('both') or lambda_c * (1 + d)^s1 ('s1only'); lambda_c = the channel's mean window
    count over the experiment. ramp: d = delta * session / (S - 1) (Q2 ramp, 0 at session 1)."""
    W = W.copy()
    if delta <= 0:
        return W
    lam = W[:, 2:, :][..., chans].mean((0, 1))
    for si in sessions:
        d = delta if not ramp else delta * si / (W.shape[0] - 1)
        k = s[si, :, 0] + (s[si, :, 1] if scenario == "both" else 0)
        mult = (1 + d) ** k - 1
        add = rng.poisson(np.outer(mult, lam))
        W[si][:, chans] = np.minimum(W[si][:, chans] + add, np.iinfo(np.int16).max)
    return W
