#!/usr/bin/env python3
"""Verify the data findings of the audit of the earlier analysis against DANDI 001611, streaming (no bulk download).
Findings are numbered as in the audit (1-4, 7, 8 and 10); Methods S1.2 of the paper's Supplemental Information summarizes them.

What it reads (DANDI 001611, version 0.260611.0634, streamed with remfile; nothing is written to disk):
  * Session A, full (trials + spikes): sub-25876/sub-25876_ses-20241111T093615_ecephys.nwb
      (subject 25876, our experiment C03_E02, session 1 of 100; authors' EXP05_SESSION001)
  * Session B, trials table only:      sub-25876/sub-25876_ses-20241111T235014_ecephys.nwb  (same experiment, session 100)
  * Subject metadata only (2 headers):  sub-26342/sub-26342_ses-20241120T120430_ecephys.nwb and
                                        sub-26342/sub-26342_ses-20241127T125335_ecephys.nwb  (finding 10, DIV)
NWB tables and columns used (read with h5py, no pynwb):
  /intervals/trials/start_time, /intervals/trials/stop_time   trial "registration" times (stored in MILLISECONDS)
  /intervals/trials/s   (256 x 2)  the two hidden binary sources s1, s2 per trial
  /intervals/trials/o   (256 x 32) the delivered 32-bit observation pattern per trial (o column k <-> k-th stim electrode)
  /units/spike_times, /units/spike_times_index, /units/channel_id   threshold detections, one "unit" per channel (ms)
  /general/extracellular_ephys/electrodes/group_name   'rec_array' (recording channels) vs 'stim_array' (32)
  /general/subject/description, /session_start_time    DIV text and recording date
Unit conversion: all times in the file are milliseconds although NWB specifies seconds; trial spacing is 1000.0
  (median diff of start_time). This script divides every time by 1000 to work in seconds.
Volley detection (there is no stimulation-event table in the files): bin all detections at 0.25 ms; a bin is
  "mass-synchronous" if >= 10% of recording channels detect in it; a trial has a volley if >= 3 mass bins fall in
  [start_time - 16 ms, start_time + 12 ms]; onset/offset = first/last such bin center.
Expected values come from our pipeline (src/organoid_anticipation, run on the sha256-verified local copies):
  tools/verify_earlier_findings_expected_values.json, embedded below.
Requirements: Python >= 3.9, numpy, h5py, remfile (pip install numpy h5py remfile). Network access to dandiarchive.org.
Usage: python tools/verify_earlier_findings.py > my_output.txt     (about 1-3 min, ~20 MB streamed)
  then: diff my_output.txt tools/verify_earlier_findings_expected.txt
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

import h5py
import numpy as np
import remfile

DANDISET, VERSION = "001611", "0.260611.0634"
API = "https://api.dandiarchive.org/api"
SESSION_A = "sub-25876/sub-25876_ses-20241111T093615_ecephys.nwb"
SESSION_B = "sub-25876/sub-25876_ses-20241111T235014_ecephys.nwb"
DIV_FILES = ["sub-26342/sub-26342_ses-20241120T120430_ecephys.nwb", "sub-26342/sub-26342_ses-20241127T125335_ecephys.nwb"]
MS = 1e-3

EXPECTED = {
    "F1": {"n_trials": 256, "n_volleys": 190, "onset_median_ms": -5.175, "onset_min_ms": -5.475, "offset_max_ms": 7.025,
           "grid_period_ms": 1000.0, "grid_resid_ms": [-0.025, 0.025], "mass_bins_outside_volley_windows": 0},
    "F2": {"window_end_to_volley_n_minus_3_ms_median": 94.8, "volleys_inside_window": 0},
    "F3": {"bins_10pct_total": 2509, "bins_10pct_within_volley_windows": 2509, "bins_at_slots": 0,
           "bins_5pct_outside_volley_windows": 206, "bins_5pct_lag_after_volley_offset_ms": [20.25, 219.25]},
    "F4": {"s_identical_session_1_vs_100": True, "o_identical_session_1_vs_100": True},
    "F7": {"n_00": 66, "n_no_bits": 66, "n_no_volley": 66, "mismatch_00_vs_no_bits": 0, "mismatch_00_vs_no_volley": 0},
    "F8": {"frac_in_artifact_main": 0.7977, "frac_in_artifact_strict": 0.7575, "frac_in_artifact_wide": 0.8056,
           "all_hz": 7.115, "artifact_free_hz": 1.456},
    "F10": {"raw_trial_spacing_median": 1000.0,
            "jitter": {"catch->catch": {"-0.05": 0, "0.0": 14, "0.05": 0}, "catch->stim": {"-0.05": 0, "0.0": 7, "0.05": 45},
                       "stim->catch": {"-0.05": 42, "0.0": 9, "0.05": 0}, "stim->stim": {"-0.05": 19, "0.0": 102, "0.05": 17}},
            "div": ["DIV 8 on 2024-11-20", "DIV 13 on 2024-11-27 (7 days later; dates give DIV 15)"]},
}


def content_url(path: str) -> str:
    q = urllib.parse.urlencode({"path": path})
    with urllib.request.urlopen(f"{API}/dandisets/{DANDISET}/versions/{VERSION}/assets/?{q}", timeout=60) as r:
        res = [a for a in json.load(r)["results"] if a["path"] == path]
    if not res:
        sys.exit(f"asset not found: {path}")
    with urllib.request.urlopen(f"{API}/assets/{res[0]['asset_id']}/", timeout=60) as r:
        urls = json.load(r)["contentUrl"]
    s3 = [u for u in urls if "s3" in u and "amazonaws" in u]
    return s3[0] if s3 else urls[0]


def open_remote(path: str) -> h5py.File:
    return h5py.File(remfile.File(content_url(path)), "r")


def s_(x):
    return x.decode() if isinstance(x, bytes) else str(x)


def mass_bins(t, n_ch, frac=0.10, bin_s=0.25e-3):
    b = np.floor(t / bin_s).astype(np.int64)
    u, c = np.unique(b, return_counts=True)
    m = c >= frac * n_ch
    return (u[m] + 0.5) * bin_s


def volleys(reg, centers, pre=0.016, post=0.012, min_bins=3):
    on = np.full(len(reg), np.nan); off = np.full(len(reg), np.nan)
    for k, t in enumerate(reg):
        lo, hi = np.searchsorted(centers, [t - pre, t + post])
        if hi - lo >= min_bins:
            on[k], off[k] = centers[lo] - t, centers[hi - 1] - t
    return on, off


def theil_sen(x, y):
    i, j = np.triu_indices(len(x), 1)
    slope = np.median((y[j] - y[i]) / (x[j] - x[i]))
    return slope, np.median(y) - slope * np.median(x)          # same convention as scipy.stats.theilslopes


def row(finding, quantity, measured, expected):
    def fmt(v):
        if isinstance(v, float):
            return f"{v:.4g}"
        if isinstance(v, (list, tuple)):
            return "[" + ", ".join(fmt(x) for x in v) + "]"
        return str(v)
    ok = "OK"
    try:
        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            ok = "OK" if abs(float(measured) - expected) <= max(1e-3, 2e-3 * abs(expected)) else "DIFFERS"
        elif isinstance(expected, list):
            ok = "OK" if np.allclose(np.asarray(measured, float), np.asarray(expected, float), atol=0.006, rtol=1e-3) else "DIFFERS"
        else:
            ok = "OK" if measured == expected else "DIFFERS"
    except Exception:  # noqa: BLE001
        ok = "CHECK"
    print(f"  {finding:4s} {quantity:70s} measured {fmt(measured):>24s} | expected {fmt(expected):>24s} | {ok}")


def main():
    print(f"DANDI {DANDISET} version {VERSION}; session A = {SESSION_A}; session B = {SESSION_B}\n")
    with open_remote(SESSION_A) as f:
        raw_start = f["intervals/trials/start_time"][:]
        s = f["intervals/trials/s"][:].astype(int)
        o = f["intervals/trials/o"][:].astype(int)
        spk = f["units/spike_times"][:] * MS
        n_rec = int((np.char.decode(f["general/extracellular_ephys/electrodes/group_name"][:].astype("S")) == "rec_array").sum())
        ident = s_(f["identifier"][()])
    reg = raw_start * MS
    spk.sort()
    print(f"Session A identifier {ident}; {len(reg)} trials; {n_rec} recording channels; {len(spk)} detections\n")

    # ---- finding 10a: units
    print("Finding 10 (units): times are stored in milliseconds")
    row("F10", "median spacing of raw start_time values (file units)", float(np.median(np.diff(raw_start))), EXPECTED["F10"]["raw_trial_spacing_median"])

    # ---- finding 1
    c10 = mass_bins(spk, n_rec)
    on, off = volleys(reg, c10)
    hv = np.isfinite(on)
    n = np.arange(len(reg))
    slope, icpt = theil_sen(n.astype(float), reg)
    resid = (reg - (icpt + slope * n)) / MS
    j = np.clip(np.searchsorted(reg, c10), 1, len(reg) - 1)
    j = np.where(np.abs(c10 - reg[j - 1]) < np.abs(c10 - reg[j]), j - 1, j)
    rel = c10 - reg[j]
    in_win = (rel >= -0.016) & (rel <= 0.012)
    print("\nFinding 1: one stimulation volley per trial, -5 to +7 ms around registration, on an exact 1-s grid")
    row("F1", "trials", len(reg), EXPECTED["F1"]["n_trials"])
    row("F1", "trials with a detected volley", int(hv.sum()), EXPECTED["F1"]["n_volleys"])
    row("F1", "volley onset re registration, median (ms)", float(np.median(on[hv]) / MS), EXPECTED["F1"]["onset_median_ms"])
    row("F1", "volley onset re registration, earliest (ms)", float(on[hv].min() / MS), EXPECTED["F1"]["onset_min_ms"])
    row("F1", "volley offset re registration, latest (ms)", float(off[hv].max() / MS), EXPECTED["F1"]["offset_max_ms"])
    row("F1", "trial period, Theil-Sen fit (ms)", float(slope / MS), EXPECTED["F1"]["grid_period_ms"])
    row("F1", "residuals from the 1-s grid, min/max (ms)", [float(resid.min()), float(resid.max())], EXPECTED["F1"]["grid_resid_ms"])
    row("F1", "10%-synchrony bins outside every volley window", int((~in_win).sum()), EXPECTED["F1"]["mass_bins_outside_volley_windows"])

    # ---- finding 2
    vol_on = reg + np.nan_to_num(on, nan=np.inf)
    gaps = [(vol_on[k - 3] - (reg[k] - 3.10)) / MS for k in range(4, len(reg)) if hv[k - 3]]
    inside = sum(int(((vol_on[hv] > reg[k] - 3.45) & (vol_on[hv] < reg[k] - 3.10)).sum()) for k in range(4, len(reg)))
    print("\nFinding 2: the 3.45-3.10 s window ends ~95 ms before trial n-3's volley")
    row("F2", "window end -> onset of trial n-3's volley, median (ms)", float(np.median(gaps)), EXPECTED["F2"]["window_end_to_volley_n_minus_3_ms_median"])
    row("F2", "volleys inside any trial's 3.45-3.10 s window", inside, EXPECTED["F2"]["volleys_inside_window"])

    # ---- finding 3
    cc = c10[~in_win]
    slots = sum(int(sum((np.abs(cc - (r - x)) < 0.020).sum() for r in reg)) for x in (2.45, 0.90, 0.50, 0.05))
    c5 = mass_bins(spk, n_rec, frac=0.05)
    j5 = np.clip(np.searchsorted(reg, c5), 1, len(reg) - 1)
    j5 = np.where(np.abs(c5 - reg[j5 - 1]) < np.abs(c5 - reg[j5]), j5 - 1, j5)
    r5 = c5 - reg[j5]
    c5 = c5[~((r5 >= -0.016) & (r5 <= 0.012))]
    offs = (reg + off)[hv]
    k5 = np.searchsorted(offs, c5, side="right") - 1
    lag = (c5[k5 >= 0] - offs[k5[k5 >= 0]]) / MS
    print("\nFinding 3: no stimulation events at 2.45, 0.90, 0.50 or 0.05 s before registration; other synchrony is evoked")
    row("F3", "10%-synchrony bins in the session", int(len(c10)), EXPECTED["F3"]["bins_10pct_total"])
    row("F3", "... of which within a volley window [-16, +12] ms", int(in_win.sum()), EXPECTED["F3"]["bins_10pct_within_volley_windows"])
    row("F3", "10% bins within 20 ms of 2.45/0.90/0.50/0.05 s before a registration", slots, EXPECTED["F3"]["bins_at_slots"])
    row("F3", "5%-synchrony bins outside volley windows", int(len(c5)), EXPECTED["F3"]["bins_5pct_outside_volley_windows"])
    row("F3", "... lag after the preceding volley offset, min/max (ms)", [float(lag.min()), float(lag.max())], EXPECTED["F3"]["bins_5pct_lag_after_volley_offset_ms"])
    print(f"       5% bins: lag after preceding volley offset, percentiles 5/50/95 = {np.round(np.percentile(lag, [5, 50, 95]), 1).tolist()} ms")

    # ---- finding 4
    with open_remote(SESSION_B) as g:
        s_b = g["intervals/trials/s"][:].astype(int); o_b = g["intervals/trials/o"][:].astype(int)
    print("\nFinding 4: the 256-trial sequence repeats across sessions (session 1 vs session 100 of the same experiment)")
    row("F4", "s identical (all 256 x 2)", bool(np.array_equal(s, s_b)), EXPECTED["F4"]["s_identical_session_1_vs_100"])
    row("F4", "o identical (all 256 x 32)", bool(np.array_equal(o, o_b)), EXPECTED["F4"]["o_identical_session_1_vs_100"])
    print("       (all 100 sessions of all 27 experiments, and no reuse across experiments, need all files; not checked here)")

    # ---- finding 7
    y = s[:, 0] + 2 * s[:, 1]
    nb = o.sum(1)
    print("\nFinding 7: no-observation trials are the (0,0) category")
    row("F7", "trials with s = (0,0)", int((y == 0).sum()), EXPECTED["F7"]["n_00"])
    row("F7", "trials with no delivered bits (o all zero)", int((nb == 0).sum()), EXPECTED["F7"]["n_no_bits"])
    row("F7", "trials with no detected volley", int((~hv).sum()), EXPECTED["F7"]["n_no_volley"])
    row("F7", "mismatches (0,0) vs no delivered bits", int(((y == 0) != (nb == 0)).sum()), EXPECTED["F7"]["mismatch_00_vs_no_bits"])
    row("F7", "mismatches (0,0) vs no volley", int(((y == 0) != ~hv).sum()), EXPECTED["F7"]["mismatch_00_vs_no_volley"])
    for cls, nm in ((1, "(1,0)"), (2, "(0,1)"), (3, "(1,1)")):
        m = y == cls
        print(f"       {nm}: fraction of bits on, bits 1-16 = {o[m, :16].mean():.3f}, bits 17-32 = {o[m, 16:].mean():.3f}")

    # ---- finding 8
    lo, hi = reg.min() - 0.5, reg.max() + 1.0
    task = spk[(spk >= lo) & (spk < hi)]
    ons, offs_ = (reg + on)[hv], (reg + off)[hv]
    res = {}
    for nm, (a, b) in dict(main=(0.004, 0.003), strict=(0.0, 0.0), wide=(0.010, 0.010)).items():
        n_in = int((np.searchsorted(task, offs_ + b, side="right") - np.searchsorted(task, ons - a)).sum())
        res[nm] = n_in / len(task)
        if nm == "main":
            free = (len(task) - n_in) / ((hi - lo) - float(((offs_ + b) - (ons - a)).sum())) / n_rec
    print("\nFinding 8: most task-period detections are stimulation artifacts (this one session; the notes' 88.9% is pooled)")
    row("F8", "fraction in [onset - 4 ms, offset + 3 ms]", res["main"], EXPECTED["F8"]["frac_in_artifact_main"])
    row("F8", "fraction in [onset, offset] (strict)", res["strict"], EXPECTED["F8"]["frac_in_artifact_strict"])
    row("F8", "fraction in [onset - 10 ms, offset + 10 ms] (wide)", res["wide"], EXPECTED["F8"]["frac_in_artifact_wide"])
    row("F8", "all detections, Hz per channel", len(task) / (hi - lo) / n_rec, EXPECTED["F8"]["all_hz"])
    row("F8", "artifact-free detections, Hz per channel", free, EXPECTED["F8"]["artifact_free_hz"])

    # ---- finding 10b: one-sample registration jitter vs no-observation status
    d = np.round(np.diff(raw_start) - 1000.0, 3)
    print("\nFinding 10 (label leak): registration spacing minus 1000 ms, by transition (counts)")
    for tr_ in ("stim->stim", "stim->catch", "catch->stim", "catch->catch"):
        a, b = tr_.split("->")
        m = (hv[:-1] == (a == "stim")) & (hv[1:] == (b == "stim"))
        meas = {str(v): int((d[m] == v).sum()) for v in (-0.05, 0.0, 0.05)}
        row("F10", f"{tr_}  (-0.05 / 0 / +0.05 ms)", [meas["-0.05"], meas["0.0"], meas["0.05"]],
            [EXPECTED["F10"]["jitter"][tr_][k] for k in ("-0.05", "0.0", "0.05")])

    # ---- finding 10c: DIV vs dates (subject metadata only)
    print("\nFinding 10 (DIV): subject description vs recording date, same subject (26342), two experiments")
    for path, exp in zip(DIV_FILES, EXPECTED["F10"]["div"]):
        with open_remote(path) as h:
            desc = s_(h["general/subject/description"][()]); date = s_(h["session_start_time"][()])[:10]
        div = desc.split("(DIV)")[-1].strip()
        row("F10", f"{path.split('/')[1][:32]}", f"DIV {div} on {date}", exp.split(" (")[0])
    print("       -> 7 calendar days apart but DIV advances by 5: the DIV field is inconsistent; derive age from dates")
    print("\nDone. 'OK' = measured matches our pipeline's value for these files; 'DIFFERS' = it does not.")


if __name__ == "__main__":
    main()
