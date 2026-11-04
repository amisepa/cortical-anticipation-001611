"""Blocked cross-validation and decoding (spec Section 6) for (session x trial) designs.

Two fold schemes over trials indexed by (session, position):
- "session_block": each session is cut into n_blocks contiguous blocks; fold b tests block b of
  *every* session, and that block's position range is the same in every session. Train = the other
  blocks, minus `gap` trials on each side of the test block.
  Because the test positions are held out in all sessions at once, a decoder can't learn a
  position -> label lookup when the label sequence repeats across sessions.
- "by_session": fold b tests whole sessions b, b+k, ... (sessions as groups). This is the naive scheme.
  It LEAKS when the sequence repeats across sessions, and is kept only to demonstrate that (A7).
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

C_GRID = np.logspace(-3, 2, 11)  # spec 6.1


def folds(session: np.ndarray, pos: np.ndarray, n_trials: int, scheme: str = "session_block",
          n_blocks: int = 5, gap: int = 5):
    """Yield (train_mask, test_mask) boolean arrays over the flattened trial index."""
    if scheme == "session_block":
        edges = np.linspace(0, n_trials, n_blocks + 1).round().astype(int)
        for b in range(n_blocks):
            lo, hi = edges[b], edges[b + 1]
            test = (pos >= lo) & (pos < hi)
            train = (pos < lo - gap) | (pos >= hi + gap)
            yield train, test
    elif scheme == "by_session":
        sess = np.unique(session)
        for b in range(n_blocks):
            ts = sess[b::n_blocks]
            test = np.isin(session, ts)
            yield ~test, test
    else:
        raise ValueError(scheme)


def _fit(X, y, C):
    m = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=2000))
    return m.fit(X, y)


def choose_C(X, y, session, pos, n_trials, gap, scheme, inner_blocks=3):
    """Inner blocked CV over C_GRID; returns the C with best mean AUC."""
    best, best_auc = C_GRID[len(C_GRID) // 2], -np.inf
    inner = list(folds(session, pos, n_trials, scheme, inner_blocks, gap))
    for C in C_GRID:
        aucs = []
        for tr, te in inner:
            if len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2:
                continue
            p = _fit(X[tr], y[tr], C).predict_proba(X[te])[:, 1]
            aucs.append(roc_auc_score(y[te], p))
        if aucs and np.mean(aucs) > best_auc:
            best, best_auc = C, np.mean(aucs)
    return best


def decode_oof(X, y, session, pos, n_trials, scheme="session_block", n_blocks=5, gap=5,
               residualize_H=None, nested=True, C_fixed=1.0, return_folds=False):
    """Out-of-fold probabilities for binary y. If residualize_H is given, X is residualized on H
    with ridge fitted on the training fold only (spec 5, cross-fitted)."""
    from sklearn.linear_model import Ridge

    p = np.full(len(y), np.nan)
    fold_id = np.full(len(y), -1)
    for b, (tr, te) in enumerate(folds(session, pos, n_trials, scheme, n_blocks, gap)):
        fold_id[te] = b
        Xtr, Xte = X[tr], X[te]
        if residualize_H is not None:
            rg = Ridge(alpha=1.0).fit(residualize_H[tr], Xtr)
            Xtr, Xte = Xtr - rg.predict(residualize_H[tr]), Xte - rg.predict(residualize_H[te])
        if nested:
            # inner folds use positions/sessions of the training set only
            C = choose_C(Xtr, y[tr], session[tr], pos[tr], n_trials, gap, scheme)
        else:
            C = C_fixed
        p[te] = _fit(Xtr, y[tr], C).predict_proba(Xte)[:, 1]
    if return_folds:
        return p, fold_id
    return p


def auc(y, p):
    """AUC on pooled out-of-fold predictions (spec 6.3 as written in v0.2)."""
    ok = ~np.isnan(p)
    return roc_auc_score(y[ok], p[ok]) if len(np.unique(y[ok])) == 2 else np.nan


def auc_per_fold(y, p, fold_id):
    """Mean of within-fold AUCs. Pooling OOF scores across folds is biased when fold-specific
    intercepts anti-correlate with fold label rates (fixed repeated sequences + position-block CV; A7)."""
    vals = [auc(y[fold_id == b], p[fold_id == b]) for b in np.unique(fold_id[fold_id >= 0])]
    return float(np.nanmean(vals)) if vals else np.nan
