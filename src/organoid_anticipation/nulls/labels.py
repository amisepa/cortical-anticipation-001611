"""Label nulls and blinding permutations (spec 8.3–8.5, CLAUDE.md blinding rule).

All functions take labels shaped (n_sessions, n_trials[, ...]) and return the same shape.
"""
from __future__ import annotations

import numpy as np


def permute_fixed(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """One random permutation of trial positions, applied identically to every session.
    Keeps any across-session repetition of the sequence (the A5 finding) while destroying the real
    position -> label assignment. Used for blinded development."""
    perm = rng.permutation(y.shape[1])
    return y[:, perm]


def permute_per_session(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Independent permutation of trial positions within each session (breaks repetition)."""
    return np.stack([yy[rng.permutation(y.shape[1])] for yy in y])


def circular_shift(y: np.ndarray, k: int, same_for_all_sessions: bool = True,
                   rng: np.random.Generator | None = None) -> np.ndarray:
    """Circular shift of the label sequence by k within each session (spec 8.4)."""
    if same_for_all_sessions:
        return np.roll(y, k, axis=1)
    ks = rng.integers(10, y.shape[1] - 10, size=y.shape[0])
    return np.stack([np.roll(yy, kk, axis=0) for yy, kk in zip(y, ks)])


def session_swap(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Pair each session's features with labels from a different session (spec 8.5).
    NOTE: degenerate (identity) when every session has the same sequence (Isomura; see A5)."""
    n = y.shape[0]
    perm = rng.permutation(n)
    while n > 1 and np.any(perm == np.arange(n)):
        perm = rng.permutation(n)
    return y[perm]


def off_by_k(y: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Target y(n+k) for trial n within session; returns (y_shifted, valid_mask)."""
    out = np.roll(y, -k, axis=1)
    valid = np.ones(y.shape[:2], bool)
    if k > 0:
        valid[:, -k:] = False
    elif k < 0:
        valid[:, :-k] = False
    return out, valid
