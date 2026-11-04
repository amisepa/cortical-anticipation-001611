"""Q1 / Q2 statistics, history residualization and position-level nulls (spec v0.3 Sections 4-6, 8).

Conventions
- Arrays are (S sessions, 256 positions, ...). Positions 0-1 are dropped from every analysis (no history).
- A "label world" is (s, o): s (S, 256, 2) hidden sources, o (S, 256, 32) delivered bits. Before CP2 the label
  world is a fixed permutation of positions applied to s and o jointly (`permute_label_world`).
- History H(n) describes the physical history of the features (real labels after CP2). Under the
  sequence-shift and sequence-swap nulls **only the target changes**; H is not shifted. Residualized features
  therefore depend only on the folds and are computed once per fold (`Prepared`), then reused for every target.
- Folds hold out the same position block in every session of the analysed set (position-aligned), with a
  5-position gap; scores are per-fold AUCs averaged over folds, then over the two sources.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score

T = 256
POS = np.arange(2, T)
N_BLOCKS, GAP = 5, 5
# Sequence-shift null: every shift in [16, 240] used exactly once, same k in every session (CP2 decision 7, D-062).
SHIFTS = np.arange(16, 241)


# ---------------------------------------------------------------- channels and features
def include_channels(W: np.ndarray, w_len: np.ndarray, thr: float = 0.01) -> np.ndarray:
    """Label-free inclusion: artifact-free rate inside the clean windows over the experiment >= thr Hz."""
    rate = W[:, 2:, :].sum((0, 1)) / w_len[:, 2:].sum()
    return rate >= thr


def spatial_pools(xy: np.ndarray, stim_xy: np.ndarray, radius: float = 100.0) -> np.ndarray:
    """0 = pool A (nearest stim electrode is an o-bit 1-16 electrode within radius), 1 = pool B (bits 17-32),
    2 = pool C (others). Uses the assumed o-column <-> stim_array-row mapping (verified in B3)."""
    d = np.sqrt(((xy[:, None, :] - stim_xy[None]) ** 2).sum(-1))
    k = d.argmin(1)
    near = d.min(1) <= radius
    return np.where(near & (k < 16), 0, np.where(near & (k >= 16), 1, 2))


def q1_features(Wsess: np.ndarray, incl: np.ndarray, pool: np.ndarray, transform: str = "log1p") -> np.ndarray:
    """(T, 4): total count and counts in pools A, B, C (included channels only), log1p (primary) or ranked within the
    session (pre-registered sensitivity; ranks are computed over all 256 positions, a label-free transform)."""
    Wi = Wsess[:, incl].astype(float)
    p = pool[incl]
    X = np.column_stack([Wi.sum(1)] + [Wi[:, p == j].sum(1) for j in range(3)])
    if transform == "log1p":
        return np.log1p(X)
    if transform == "rank":
        from scipy.stats import rankdata
        return np.column_stack([rankdata(c) / len(c) for c in X.T])
    raise ValueError(transform)


# ---------------------------------------------------------------- label world and history
def permute_label_world(s: np.ndarray, o: np.ndarray, rng: np.random.Generator):
    """One permutation of positions applied identically to every session (keeps the repetition)."""
    perm = rng.permutation(s.shape[1])
    return s[:, perm], o[:, perm]


def _lag(a: np.ndarray, k: int) -> np.ndarray:
    out = np.zeros_like(a)
    out[:, k:] = a[:, :-k]
    return out


def history(s: np.ndarray, o: np.ndarray, R: np.ndarray, incl: np.ndarray, pool: np.ndarray,
            W: np.ndarray | None = None, q2: bool = False) -> np.ndarray:
    """H(n) for every (session, position): (S, T, d). Spec 5.
    Q1 (11): s(n-1) x2, s(n-2) x2, o(n-1) bits 1-16 and 17-32 counts, log1p r(n-1) total + pools x4, position.
    Q2 adds: session index, previous-session mean log1p clean total, cumulative pulses before n,
    s frequencies over the last 10 and 50 trials (x4)."""
    S = s.shape[0]
    sf = s.astype(float)
    r_prev = _lag(np.log1p(np.concatenate([R[..., incl].sum(-1, keepdims=True)] +
                                          [R[..., incl][..., pool[incl] == j].sum(-1, keepdims=True) for j in range(3)], -1).astype(float)), 1)
    o_half = np.stack([o[..., :16].sum(-1), o[..., 16:].sum(-1)], -1).astype(float)
    pos = np.broadcast_to(np.arange(T)[None, :, None] / T, (S, T, 1))
    H = [_lag(sf, 1), _lag(sf, 2), _lag(o_half, 1), r_prev, pos]
    if q2:
        sess = np.broadcast_to((np.arange(S) / max(S - 1, 1))[:, None, None], (S, T, 1))
        tot = np.log1p(W[..., incl].sum(-1).astype(float))[:, 2:].mean(1)
        prev_tot = np.r_[tot[0], tot[:-1]]
        prev_tot = np.broadcast_to(prev_tot[:, None, None], (S, T, 1))
        cum = _lag(np.cumsum(o.sum(-1), axis=1)[..., None].astype(float), 1) / (32 * T)
        freqs = []
        for w in (10, 50):
            c = np.cumsum(np.concatenate([np.zeros((S, 1, 2)), sf], 1), axis=1)
            idx = np.arange(T)
            lo = np.maximum(idx - w, 0)
            f = (c[:, idx] - c[:, lo]) / np.maximum(idx - lo, 1)[None, :, None]   # mean of s over trials [n-w, n-1]
            freqs.append(f)
        H += [sess, prev_tot, cum] + freqs
    return np.concatenate([np.asarray(h, float) for h in H], -1)


# ---------------------------------------------------------------- folds, residualization, decoding
def folds(pos: np.ndarray):
    edges = np.linspace(0, T, N_BLOCKS + 1).round().astype(int)
    for b in range(N_BLOCKS):
        lo, hi = edges[b], edges[b + 1]
        yield (pos < lo - GAP) | (pos >= hi + GAP), (pos >= lo) & (pos < hi)


@dataclass
class Prepared:
    """Residualized, standardized features per fold; independent of the target."""
    Xtr: list
    Xte: list
    tr: list
    te: list
    pos: np.ndarray   # position of each row
    row_sess: np.ndarray


def prepare(X: np.ndarray, H: np.ndarray, pos: np.ndarray, row_sess: np.ndarray,
            Rch: np.ndarray | None = None, n_pc: int = 5, residualize: bool = True) -> Prepared:
    """X (n, p) features, H (n, d) history, Rch (n, q) per-channel log1p r(n-1) for in-fold PCs (Q2)."""
    Xtr, Xte, trs, tes = [], [], [], []
    for tr, te in folds(pos):
        A, B = X[tr], X[te]
        if residualize:
            Ht, He = H[tr], H[te]
            if Rch is not None and n_pc:
                pca = PCA(n_pc, random_state=0).fit(Rch[tr])
                Ht = np.column_stack([Ht, pca.transform(Rch[tr])])
                He = np.column_stack([He, pca.transform(Rch[te])])
            mu, sd = Ht.mean(0), Ht.std(0)
            sd[sd == 0] = 1
            Ht, He = (Ht - mu) / sd, (He - mu) / sd
            rg = Ridge(alpha=1.0).fit(Ht, A)
            A, B = A - rg.predict(Ht).reshape(A.shape), B - rg.predict(He).reshape(B.shape)   # 1-column X: predict is 1-D
        mu, sd = A.mean(0), A.std(0)
        sd[sd == 0] = 1
        Xtr.append((A - mu) / sd); Xte.append((B - mu) / sd); trs.append(tr); tes.append(te)
    return Prepared(Xtr, Xte, trs, tes, pos, row_sess)


def score(P: Prepared, y: np.ndarray, C: float = 1.0) -> float:
    """Mean of within-fold AUCs for binary target y (rows aligned with P)."""
    aucs = []
    for A, B, tr, te in zip(P.Xtr, P.Xte, P.tr, P.te):
        yt, ye = y[tr], y[te]
        if len(np.unique(yt)) < 2 or len(np.unique(ye)) < 2:
            continue
        m = LogisticRegression(C=C, max_iter=1000).fit(A, yt)
        aucs.append(roc_auc_score(ye, m.decision_function(B)))
    return float(np.mean(aucs)) if aucs else np.nan


def score2(P: Prepared, Y: np.ndarray, C: float = 1.0) -> float:
    """Mean over the two sources. Y (n, 2)."""
    return float(np.mean([score(P, Y[:, j], C) for j in range(Y.shape[1])]))


def shift_targets(s_seq: np.ndarray, k: int) -> np.ndarray:
    """Sequence-shift null target: y_k(n) = y((n + k) mod 256), same k in every session. s_seq (S, T, 2).
    Also used for lagged targets: k = -1 gives s(n-1), k = 5 gives s(n+5) (within-session circular; positions >= 2
    only are analysed, so s(n-1) never wraps)."""
    return np.roll(s_seq, -k, axis=1)


# ---------------------------------------------------------------- Q1 and Q2
def q1_prepare(W, R, s, o, incl, pool, sess=0, residualize=True, transform="log1p", keep=None) -> tuple[Prepared, np.ndarray]:
    """keep: optional (S, T) bool mask of analysable trials (w_ok; spec 3). Excluded positions are dropped as rows; the
    history of the remaining rows is unchanged (physical history). Targets must be indexed with P.pos (targets_for)."""
    pos = POS if keep is None else POS[keep[sess, POS]]
    X = q1_features(W[sess], incl, pool, transform)[pos]
    H = history(s[sess:sess + 1], o[sess:sess + 1], R[sess:sess + 1], incl, pool)[0][pos]
    P = prepare(X, H, pos, np.zeros(len(pos), int), residualize=residualize)   # row_sess relative to s[sess:sess+1]
    return P, s[sess][pos]


def q2_block_rows(S_block: np.ndarray, keep=None):
    pos = np.tile(POS, len(S_block))
    rs = np.repeat(S_block, len(POS))
    if keep is not None:
        m = keep[rs, pos]
        pos, rs = pos[m], rs[m]
    return pos, rs


def q2_prepare(W, R, s, o, incl, pool, sessions, residualize=True, Hfull=None, keep=None) -> Prepared:
    """Per-channel log1p W features for the given sessions (one block), position-aligned folds. keep: as q1_prepare."""
    Hfull = history(s, o, R, incl, pool, W=W, q2=True) if Hfull is None else Hfull
    pos, rs = q2_block_rows(sessions, keep)
    X = np.log1p(W[rs, pos][:, incl].astype(float))
    H = Hfull[rs, pos]
    Rch = np.log1p(R[rs, pos - 1][:, incl].astype(float))    # per-channel r(n-1) for in-fold PCs
    return prepare(X, H, pos, rs, Rch=Rch if residualize else None, residualize=residualize)


def q2_growth(block_aucs: np.ndarray) -> float:
    """G = 9 x OLS slope of block AUC on block index (fitted change block 1 -> block 10)."""
    b = np.arange(len(block_aucs))
    ok = np.isfinite(block_aucs)
    return float((len(block_aucs) - 1) * np.polyfit(b[ok], block_aucs[ok], 1)[0])


def q2_blocks(n_sessions: int = 100, n_blocks: int = 10):
    return [np.arange(b * n_sessions // n_blocks, (b + 1) * n_sessions // n_blocks) for b in range(n_blocks)]


def targets_for(P: Prepared, s_seq_world: np.ndarray) -> np.ndarray:
    """Rows of a Prepared block -> (n, 2) targets from a (S, T, 2) label array."""
    return s_seq_world[P.row_sess, P.pos]


def design_report(H: np.ndarray, names: list[str] | None = None) -> dict:
    """B1: rank of the history design and constant columns (logged; ridge keeps the fit defined either way)."""
    H = np.asarray(H, float)
    sd = H.std(0)
    const = np.flatnonzero(sd == 0)
    Hs = (H[:, sd > 0] - H[:, sd > 0].mean(0)) / sd[sd > 0]
    rank = int(np.linalg.matrix_rank(Hs)) if Hs.size else 0
    nm = names or [f"h{i}" for i in range(H.shape[1])]
    return dict(n_cols=H.shape[1], n_nonconstant=int((sd > 0).sum()), rank_nonconstant=rank,
                full_rank=rank == int((sd > 0).sum()), constant_cols=[nm[i] for i in const])


H_NAMES_Q1 = ["s1(n-1)", "s2(n-1)", "s1(n-2)", "s2(n-2)", "o1-16(n-1)", "o17-32(n-1)",
              "r_tot(n-1)", "r_A(n-1)", "r_B(n-1)", "r_C(n-1)", "position"]
H_NAMES_Q2 = H_NAMES_Q1 + ["session", "prev_session_clean_rate", "cum_pulses",
                           "f10_s1", "f10_s2", "f50_s1", "f50_s2"]
