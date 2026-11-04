"""Per-experiment 001611 pipeline (Phase B): timeline, pre-stimulus window, features, descriptive decay.

One pass over the session files of an experiment:
  1. read spikes and trials (reader converts ms -> s), detect volleys label-free (events/volleys.py)
  2. engine grid per session (Theil-Sen), t0 = grid + experiment-median volley onset offset (spec 2)
  3. pre-stimulus window W(n) = [t0 - g - L, t0 - g], **one fixed L = 250 ms for every experiment** (CP2 decision 1,
     D-059). The window must be stimulation-free: a trial whose window overlaps the blanking span [onset - 4 ms,
     offset + 3 ms] of any detected volley is flagged (w_ok = False) and excluded from analysis (spec 3, trials; D-060).
     The window is NOT free of carryover from trial n-1; carryover is handled by history residualization and the
     sequence-shift null.
     No experiment is excluded or shortened on the basis of a response window.
  4. per-channel counts in W(n); post-stimulus counts per channel in [t0 + 25 ms, t0 + 300 ms] (8.2; r(n-1) in H)
  5. descriptive only (spec 8.13): evoked decay vs time since the last volley offset, pooled and (if `use_labels`) by
     the category of the evoking trial; response windows against (a) the pre-task baseline (old rule, kept for
     reference) and (b) the label-free within-task reference = clean-window rate on trials whose previous trial had no
     volley; label-free carryover ratio = clean-window rate after a volley / after no volley.

Label use: labels (s, o) are only stored for dev experiments (`use_labels=True`, and in the confirmatory run). The
within-task reference and the carryover ratio condition on "previous trial had a volley", which is equivalent to the
previous trial's no-observation label, so they are computed only when `use_labels=True` (conservative blinding; D-059).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from organoid_anticipation.events.volleys import trial_volleys
from organoid_anticipation.io.d001611 import read_session

G = 0.015            # guard (D-004b, CP1)
L = 0.250            # fixed window length (CP2 decision 1, D-059)
RW_FACTOR = 1.1      # descriptive response-window band (+-10%)
POST = (0.025, 0.300)
BIN = 0.005
EDGES = np.arange(0, 3.0 + BIN, BIN)
BLANK = (0.004, 0.003)  # blanking spans around volleys (D-007b)
HOLD_BINS = 5        # descriptive RW: last run of >= 25 ms outside the band, before 970 ms


@dataclass
class Experiment:
    experiment_id: str
    session_ids: list
    channel_ids: np.ndarray        # recording channels (common to all sessions)
    xy: np.ndarray                 # (n_ch, 2) um
    stim_xy: np.ndarray            # (32, 2) um, row k <-> o column k (verified in B3)
    t0: np.ndarray                 # (S, 256) s, session clock
    has_volley: np.ndarray         # (S, 256) bool
    w_start: np.ndarray            # (S, 256)
    w_len: np.ndarray              # (S, 256)
    w_ok: np.ndarray               # (S, 256) bool: window stimulation-free (no overlap with any volley blanking span)
    W: np.ndarray                  # (S, 256, n_ch) int16 counts in W(n)
    R: np.ndarray                  # (S, 256, n_ch) int16 counts in [t0+25, t0+300] ms
    s: np.ndarray | None = None    # (S, 256, 2) uint8 (labels available)
    o: np.ndarray | None = None    # (S, 256, 32) uint8 (labels available)
    meta: dict = field(default_factory=dict)
    decay: pd.DataFrame | None = None


def _counts(sp_t, sp_ch, starts, ends, n_ch):
    """Per-trial, per-channel counts of spikes in [starts, ends). Windows must not overlap."""
    order = np.argsort(starts)
    st, en = starts[order], ends[order]
    k = np.searchsorted(st, sp_t, side="right") - 1
    ok = (k >= 0)
    ok[ok] &= sp_t[ok] < en[k[ok]]
    out = np.zeros((len(starts), n_ch), np.int32)
    np.add.at(out, (order[k[ok]], sp_ch[ok]), 1)
    return out


def _smooth(rate):
    return pd.Series(rate).rolling(5, center=True, min_periods=1).mean().values


def rw_last_above(rate, base, win_max=0.970):
    """Old CP1/CP2 rule (descriptive only): last 25-ms-smoothed bin > 1.1 x base before 970 ms."""
    sm = _smooth(rate)
    mid = EDGES[:-1] + BIN / 2
    above = np.flatnonzero((sm > RW_FACTOR * base) & (mid < win_max) & np.isfinite(sm))
    return float(mid[above.max() + 1] - BIN / 2) if len(above) else 0.0


def rw_band(rate, ref, two_sided=True, win_max=0.970):
    """Descriptive: end of the last run of >= 25 ms in which the smoothed rate is outside [ref/1.1, 1.1 ref]
    (two-sided) or above 1.1 ref (one-sided), before 970 ms. 0.970 means 'not back in band within the observable range'."""
    sm = _smooth(rate)
    mid = EDGES[:-1] + BIN / 2
    ok = (mid < win_max) & np.isfinite(sm)
    out = (sm > RW_FACTOR * ref) | ((sm < ref / RW_FACTOR) if two_sided else False)
    out &= ok
    run, last = 0, 0.0
    for i in range(len(mid)):
        run = run + 1 if out[i] else 0
        if run >= HOLD_BINS:
            last = mid[i] + BIN / 2
    return float(min(last, win_max))


def build_experiment(paths: list[Path], session_ids: list[str], experiment_id: str, use_labels: bool,
                     L_win: float = L) -> Experiment:
    """L_win: window length (primary 0.250 s; pre-registered sensitivity 0.360 s, the former 'RW = 610 ms' variant)."""
    sess = []
    for p, sid in zip(paths, session_ids):
        S = read_session(p, dict(session_id=sid))
        tr, sp = S.trials, S.spikes
        v, extra = trial_volleys(tr.t_start.values, sp.t.values, S.meta["n_rec_channels"])
        n = tr.trial_idx.values
        ts = stats.theilslopes(tr.t_start.values, n)
        sess.append(dict(sid=sid, tr=tr, sp=sp, v=v, ch=S.channels, stim=S.stim_electrodes, meta=S.meta,
                         grid=ts.intercept + ts.slope * n, slope=ts.slope, n_extra=len(extra)))
    ch0 = sess[0]["ch"].sort_values("channel_id")
    for d in sess:
        if not np.array_equal(np.sort(d["ch"].channel_id.values), ch0.channel_id.values):
            raise ValueError(f"channel configuration differs within {experiment_id}: {d['sid']}")
    chan = ch0.channel_id.values
    n_ch = len(chan)
    on_med = float(np.nanmedian(np.concatenate([d["v"].on_rel_s.values for d in sess])))
    S_, T = len(sess), 256

    # ---- pass A (descriptive): decay histograms (pooled and by evoking category) and pre-task baseline
    counts = {"all": np.zeros(len(EDGES) - 1)}
    occ = {"all": np.zeros(len(EDGES) - 1)}
    base_n, base_t = 0, 0.0
    for d in sess:
        tr, v = d["tr"], d["v"]
        sp = np.sort(d["sp"].t.values)
        hv = v.has_volley.values
        ons = (tr.t_start.values + v.on_rel_s.values)[hv]
        offs = (tr.t_start.values + v.off_rel_s.values)[hv]
        cats = (tr.y1.values[hv] if use_labels else np.zeros(hv.sum(), int))
        lo, hi = 0.05, ons[0] - 0.01
        base_n += np.searchsorted(sp, hi) - np.searchsorted(sp, lo)
        base_t += (hi - lo) * n_ch
        k = np.searchsorted(offs, sp, side="right") - 1
        j = np.searchsorted(ons, sp, side="right") - 1
        in_v = (j >= 0) & (sp <= offs[np.clip(j, 0, None)])
        ok = (k >= 0) & ~in_v
        dt = sp[ok] - offs[k[ok]]
        kc = cats[k[ok]]
        nxt = np.searchsorted(ons, offs, side="right")
        span = np.where(nxt < len(ons), ons[np.clip(nxt, 0, len(ons) - 1)] - offs, tr.t_stop.max() - offs)
        o_v = np.clip(span[:, None] - EDGES[None, :-1], 0, BIN)
        counts["all"] += np.histogram(dt, EDGES)[0] / n_ch
        occ["all"] += o_v.sum(0)
        if use_labels:
            for c in (1, 2, 3):
                counts.setdefault(c, np.zeros(len(EDGES) - 1))
                occ.setdefault(c, np.zeros(len(EDGES) - 1))
                counts[c] += np.histogram(dt[kc == c], EDGES)[0] / n_ch
                occ[c] += o_v[cats == c].sum(0)
    base = base_n / base_t
    decay = pd.DataFrame({"t_since_volley_off_s": EDGES[:-1] + BIN / 2})
    for key in counts:
        decay[f"rate_{key}"] = np.where(occ[key] > 0, counts[key] / np.maximum(occ[key], 1e-12), np.nan)
        decay[f"occ_{key}"] = occ[key]

    # ---- pass B: fixed windows and features
    t0 = np.zeros((S_, T)); hv_all = np.zeros((S_, T), bool)
    w_start = np.zeros((S_, T)); w_len = np.zeros((S_, T)); w_ok = np.ones((S_, T), bool)
    W = np.zeros((S_, T, n_ch), np.int16); R = np.zeros((S_, T, n_ch), np.int16)
    s_arr = np.zeros((S_, T, 2), np.uint8) if use_labels else None
    o_arr = np.zeros((S_, T, 32), np.uint8) if use_labels else None
    min_gap_after_prev_off = np.inf
    for i, d in enumerate(sess):
        tr, v = d["tr"], d["v"]
        t0_i = d["grid"] + on_med
        hv = v.has_volley.values
        start, end = t0_i - G - L_win, t0_i - G
        # stimulation-free: no volley blanking span [onset - 4 ms, offset + 3 ms] of ANY trial overlaps any window
        on_abs = (tr.t_start.values + v.on_rel_s.values)[hv] - BLANK[0]
        off_abs = (tr.t_start.values + v.off_rel_s.values)[hv] + BLANK[1]
        jj = np.searchsorted(on_abs, end, side="left") - 1          # last span starting before the window end
        valid = jj >= 0
        overlap = np.zeros(T, bool)
        overlap[valid] = off_abs[jj[valid]] > start[valid]
        w_ok[i] = ~overlap
        prev_ok = valid & ~overlap
        if prev_ok.any():
            min_gap_after_prev_off = min(min_gap_after_prev_off, float((start[prev_ok] - off_abs[jj[prev_ok]]).min()))
        t0[i], hv_all[i], w_start[i], w_len[i] = t0_i, hv, start, end - start
        spd = d["sp"]
        ci = np.searchsorted(chan, spd.channel_id.values)
        ts_ = spd.t.values
        W[i] = np.minimum(_counts(ts_, ci, start, end, n_ch), np.iinfo(np.int16).max)
        R[i] = np.minimum(_counts(ts_, ci, t0_i + POST[0], t0_i + POST[1], n_ch), np.iinfo(np.int16).max)
        if use_labels:
            s_arr[i] = tr[["s1", "s2"]].values
            o_arr[i] = np.array([list(map(int, b)) for b in tr.o_bits])

    # ---- descriptive response windows and carryover (8.13; spec 2)
    rw_base = {str(k): rw_last_above(decay[f"rate_{k}"].values, base) for k in counts}
    desc = dict(rw_vs_pretask_baseline_s=rw_base)
    if use_labels:
        rate = W[:, 2:, :].sum(-1) / w_len[:, 2:] / n_ch
        prev_v = hv_all[:, 1:-1]
        ok = w_ok[:, 2:]
        ref = float(rate[~prev_v & ok].mean())                  # within-task reference (after a no-volley trial)
        desc.update(within_task_ref_hz=ref, ref_over_pretask=ref / base,
                    carryover_ratio=float(rate[prev_v & ok].mean() / ref),
                    rw_vs_within_task_two_sided_s={str(k): rw_band(decay[f"rate_{k}"].values, ref, True) for k in counts},
                    rw_vs_within_task_elevation_s={str(k): rw_band(decay[f"rate_{k}"].values, ref, False) for k in counts})
    stim = sess[0]["stim"]
    meta = dict(experiment_id=experiment_id, n_sessions=S_, n_channels=n_ch, onset_offset_s=on_med,
                window_len_s=L_win, window_rule="fixed [t0 - 15 ms - L, t0 - 15 ms], no RW exclusion (D-059)",
                excluded=None, base_rate_hz=base, period_s=[d["slope"] for d in sess],
                min_gap_window_start_after_prev_volley_span_s=min_gap_after_prev_off,
                n_windows_overlapping_volley_span=int((~w_ok).sum()),
                windows_overlapping_volley_span=[[sess[i]["sid"], int(n)] for i, n in zip(*np.nonzero(~w_ok))],
                n_unattributed_mass_bins=int(sum(d["n_extra"] for d in sess)),
                identifiers=[d["meta"]["identifier"] for d in sess],
                subject_description=sess[0]["meta"]["subject_description"], **desc)
    return Experiment(experiment_id, list(session_ids), chan, ch0[["x_um", "y_um"]].values,
                      stim[["x_um", "y_um"]].values, t0, hv_all, w_start, w_len, w_ok, W, R, s_arr, o_arr, meta, decay)


def save(exp: Experiment, path: Path):
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays = dict(channel_ids=exp.channel_ids, xy=exp.xy, stim_xy=exp.stim_xy, t0=exp.t0, has_volley=exp.has_volley,
                  w_start=exp.w_start, w_len=exp.w_len, w_ok=exp.w_ok, W=exp.W, R=exp.R, session_ids=np.array(exp.session_ids))
    if exp.s is not None:
        arrays.update(s=exp.s, o=exp.o)
    np.savez_compressed(path, **arrays)
    path.with_suffix(".json").write_text(json.dumps(exp.meta, indent=1, default=float))
    if exp.decay is not None:
        exp.decay.to_csv(path.with_name(path.stem + "_decay.csv"), index=False)


def load(path: Path) -> dict:
    import json
    path = Path(path)
    z = dict(np.load(path, allow_pickle=False))
    if "w_ok" not in z:
        raise ValueError(f"{path}: build predates D-060 (no w_ok mask); rebuild with scripts/B1_build_experiments.py")
    z["meta"] = json.loads(path.with_suffix(".json").read_text())
    return z
