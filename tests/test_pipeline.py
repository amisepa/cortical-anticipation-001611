import numpy as np
import pytest

from organoid_anticipation.models.pooling import bf10, tost
from organoid_anticipation.pipeline import analysis as A


def _world(S=3, seed=0):
    rng = np.random.default_rng(seed)
    s = np.tile(rng.integers(0, 2, (1, A.T, 2)), (S, 1, 1)).astype(np.uint8)
    o = np.zeros((S, A.T, 32), np.uint8)
    o[..., :16] = s[..., :1]
    o[..., 16:] = s[..., 1:]
    return s, o


def test_folds_hold_out_positions_with_gap():
    pos = np.tile(A.POS, 4)
    seen = np.zeros(len(pos), bool)
    for tr, te in A.folds(pos):
        assert not (tr & te).any()
        lo, hi = pos[te].min(), pos[te].max()
        assert not ((pos[tr] >= lo - A.GAP) & (pos[tr] <= hi + A.GAP)).any()
        seen |= te
    assert seen.all()


def test_shift_targets_same_k_every_session():
    s, _ = _world()
    sh = A.shift_targets(s, 7)
    assert np.array_equal(sh[:, 0], s[:, 7]) and (sh == sh[0]).all()


def test_history_lags():
    s, o = _world()
    R = np.zeros((3, A.T, 10), np.int16)
    incl = np.ones(10, bool)
    pool = np.array([0] * 3 + [1] * 3 + [2] * 4)
    H = A.history(s, o, R, incl, pool)
    assert H.shape[-1] == len(A.H_NAMES_Q1)
    assert np.array_equal(H[:, 5, 0], s[:, 4, 0]) and np.array_equal(H[:, 5, 3], s[:, 3, 1])
    W = np.ones((3, A.T, 10), np.int16)
    H2 = A.history(s, o, R, incl, pool, W=W, q2=True)
    assert H2.shape[-1] == len(A.H_NAMES_Q2)


def test_design_report_flags_constant():
    H = np.column_stack([np.ones(50), np.arange(50), 2 * np.arange(50)])
    r = A.design_report(H, ["c", "a", "b"])
    assert r["constant_cols"] == ["c"] and not r["full_rank"]


def test_growth_is_fitted_change():
    a = 0.5 + 0.01 * np.arange(10)
    assert A.q2_growth(a) == pytest.approx(0.09)


def test_prepare_independent_of_target_and_detects_signal():
    rng = np.random.default_rng(1)
    S = 4
    pos, rs = np.tile(A.POS, S), np.repeat(np.arange(S), len(A.POS))
    y = rng.integers(0, 2, len(pos))
    X = rng.normal(size=(len(pos), 5)); X[:, 0] += 1.0 * y
    H = rng.normal(size=(len(pos), 3))
    P = A.prepare(X, H, pos, rs)
    assert A.score(P, y) > 0.65
    assert abs(A.score(P, rng.permutation(y)) - 0.5) < 0.1


def test_spatial_pools():
    stim = np.array([[0, 0]] * 16 + [[1000, 0]] * 16, float)
    xy = np.array([[10, 0], [990, 0], [500, 0]], float)
    assert list(A.spatial_pools(xy, stim)) == [0, 1, 2]


def test_tost_and_bf():
    assert tost(0.0, 0.005, 10, 0.03)["equivalent"]
    assert not tost(0.0, 0.05, 10, 0.03)["equivalent"]
    assert bf10(0.0, 0.01, 0.03) < 1 < bf10(0.08, 0.01, 0.03)


def test_shift_set_is_16_to_240_once():
    assert A.SHIFTS.min() == 16 and A.SHIFTS.max() == 240 and len(np.unique(A.SHIFTS)) == len(A.SHIFTS) == 225


def test_keep_mask_drops_rows_and_targets_follow():
    s, o = _world(S=1, seed=3)
    rng = np.random.default_rng(0)
    W = rng.poisson(2, (1, A.T, 10)).astype(np.int16)
    R = rng.poisson(2, (1, A.T, 10)).astype(np.int16)
    incl = np.ones(10, bool); pool = np.array([0] * 3 + [1] * 3 + [2] * 4)
    keep = np.ones((1, A.T), bool); keep[0, 50] = False
    P, Y = A.q1_prepare(W, R, s, o, incl, pool, keep=keep)
    assert 50 not in P.pos and len(P.pos) == len(A.POS) - 1
    assert np.array_equal(Y, A.targets_for(P, s))


def test_top8_picks_busiest_included_channels():
    from organoid_anticipation.synth.inject import channel_subset
    W = np.zeros((2, A.T, 20), np.int16)
    W[..., :] = np.arange(20)[None, None, :]
    incl = np.ones(20, bool); incl[19] = False
    ch = channel_subset("top8", incl, np.zeros(20, int), W, np.random.default_rng(0))
    assert sorted(ch) == list(range(11, 19))


def test_prepare_single_feature_column():
    rng = np.random.default_rng(2)
    pos = A.POS.copy()
    X = rng.normal(size=(len(pos), 1)); H = rng.normal(size=(len(pos), 3))
    P = A.prepare(X, H, pos, np.zeros(len(pos), int))
    assert all(b.shape[1] == 1 for b in P.Xte)
