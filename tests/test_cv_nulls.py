import numpy as np

from organoid_anticipation.decode.blocked_cv import auc, decode_oof, folds
from organoid_anticipation.nulls.labels import off_by_k, permute_fixed, permute_per_session
from organoid_anticipation.synth.inject import inject_counts


def _grid(S=10, T=100):
    return np.repeat(np.arange(S), T), np.tile(np.arange(T), S)


def test_session_block_folds_partition_and_gap():
    sess, pos = _grid()
    test_union = np.zeros(len(pos), bool)
    for tr, te in folds(sess, pos, 100, "session_block", 5, 5):
        assert not (tr & te).any()
        assert np.unique(pos[te]).size == 20               # same positions in every session
        lo, hi = pos[te].min(), pos[te].max()
        assert not ((pos[tr] >= lo - 5) & (pos[tr] <= hi + 5)).any()
        test_union |= te
    assert test_union.all()


def test_permute_fixed_keeps_repetition():
    rng = np.random.default_rng(0)
    y = np.tile(rng.integers(0, 2, 100), (10, 1))
    yp = permute_fixed(y, rng)
    assert (yp == yp[0]).all()
    yq = permute_per_session(y, rng)
    assert not (yq == yq[0]).all()


def test_off_by_k():
    y = np.arange(20).reshape(2, 10)
    yk, v = off_by_k(y, 3)
    assert yk[0, 0] == 3 and not v[0, -3:].any() and v[0, :7].all()


def test_position_leak_vs_block_cv():
    """A fixed sequence repeated over sessions is perfectly decodable from position under by-session CV,
    and not under session-block CV."""
    rng = np.random.default_rng(1)
    S, T = 10, 100
    sess, pos = _grid(S, T)
    y = np.tile(rng.integers(0, 2, T), S)
    X = np.eye(T)[pos]
    a_leak = auc(y, decode_oof(X, y, sess, pos, T, "by_session", nested=False))
    a_block = auc(y, decode_oof(X, y, sess, pos, T, "session_block", nested=False))
    assert a_leak > 0.95 and abs(a_block - 0.5) < 0.15


def test_injection_detectable():
    rng = np.random.default_rng(2)
    S, T = 20, 100
    sess, pos = _grid(S, T)
    y = rng.integers(0, 2, S * T)
    X = rng.poisson(5, size=(S * T, 16)).astype(float)
    Xi = inject_counts(X, y, 0.5, np.arange(4), rng)
    assert auc(y, decode_oof(Xi, y, sess, pos, T, "session_block", nested=False)) > 0.6
