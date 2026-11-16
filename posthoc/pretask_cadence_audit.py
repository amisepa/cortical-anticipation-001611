# Copyright 2026 Cedric Cannard and William Reid
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare population-spike autocorrelation before and after task onset.

For each session, the pre-task interval [0, duration) is compared with an equally long
interval beginning at the first trial. The pre-task segment ends at the last 10-ms bin
boundary at or before 16 ms before the first trial, so the leading edge of the first
volley (about 5 ms before registration) cannot fall in its last bin.

The task interval is a positive control: it contains the known once-per-second events.
Its autocorrelation is computed twice, once with volley detections kept and once with
the bins within 16 ms before to 12 ms after each trial time excluded, which separates
the stimulation clock from any residual structure. Population spikes are binned at
10 ms. Normalized autocorrelations are calculated at lags 0.10-2.00 s and averaged
within each culture.
"""
import argparse
import glob
import os

import h5py
import numpy as np

BIN_S = 0.01
LAGS = np.arange(10, 201)
PRE_GAP_S = 0.016
MASK_BEFORE_S = 0.016
MASK_AFTER_S = 0.012


def autocorrelation(counts, valid=None):
    """Normalized autocovariance with overlap-length correction.

    Bins where valid is False are excluded from the mean, the variance and every
    lagged product, so masked intervals do not contribute to any lag.
    """
    x = counts.astype(np.float64)
    if valid is None:
        valid = np.ones(len(x), dtype=bool)
    if valid.sum() < 10:
        return np.full(len(LAGS), np.nan)
    x = x - x[valid].mean()
    var = np.mean(x[valid] ** 2)
    if not np.isfinite(var) or var == 0:
        return np.full(len(LAGS), np.nan)
    out = np.full(len(LAGS), np.nan)
    for k, lag in enumerate(LAGS):
        pair = valid[:-lag] & valid[lag:]
        if pair.sum() >= 10:
            out[k] = np.mean(x[:-lag][pair] * x[lag:][pair]) / var
    return out


def find_files(data_dir):
    """Accept both DANDI layouts: sub-<id>/<file>.nwb and sub-<id>_dl/<file>.nwb."""
    for folder, pattern in (("sub-*", "*.nwb"), ("sub-*_dl", "*.nwb")):
        files = sorted(glob.glob(os.path.join(data_dir, folder, pattern)))
        if files:
            return files
    return sorted(glob.glob(os.path.join(data_dir, "sub-*", "**", "*.nwb"), recursive=True))


def one_session(path):
    culture = os.path.basename(os.path.dirname(path)).split("_")[0]
    with h5py.File(path, "r") as f:
        spikes = np.asarray(f["units/spike_times"], dtype=np.float64) / 1000.0
        starts = np.asarray(f["intervals/trials/start_time"], dtype=np.float64) / 1000.0
        n_units = len(f["units/id"])
    duration = np.floor((starts[0] - PRE_GAP_S) / BIN_S) * BIN_S
    edges = np.arange(0, duration + BIN_S / 2, BIN_S)
    pre = spikes[(spikes >= 0) & (spikes < duration)]
    task = spikes[(spikes >= duration) & (spikes < 2 * duration)] - duration
    task_counts = np.histogram(task, bins=edges)[0]
    centres = edges[:-1] + BIN_S / 2
    valid = np.ones(len(task_counts), dtype=bool)
    for start in starts:
        relative = start - duration
        valid &= ~((centres >= relative - MASK_BEFORE_S) & (centres <= relative + MASK_AFTER_S))
    return {
        "culture": culture,
        "path": path,
        "duration": duration,
        "n_units": n_units,
        "pre_n": int(len(pre)),
        "pre_rate": len(pre) / duration / n_units if duration > 0 else np.nan,
        "pre_ac": autocorrelation(np.histogram(pre, bins=edges)[0]),
        "task_ac": autocorrelation(task_counts),
        "task_ac_masked": autocorrelation(task_counts, valid),
        "masked_fraction": 1.0 - valid.mean(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data/raw/d001611")
    parser.add_argument("--out", default="posthoc/output/pretask_cadence_all.npz")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--jobs", type=int, default=1, help="parallel workers (needs joblib)")
    args = parser.parse_args()

    files = find_files(args.data_dir)[::args.stride]
    if args.max_files is not None:
        files = files[:args.max_files]
    if not files:
        raise RuntimeError("No NWB files found under " + args.data_dir)

    if args.jobs > 1:
        from joblib import Parallel, delayed
        rows = Parallel(n_jobs=args.jobs, verbose=5)(delayed(one_session)(p) for p in files)
    else:
        rows = []
        for i, path in enumerate(files):
            rows.append(one_session(path))
            if (i + 1) % 100 == 0 or i + 1 == len(files):
                print("%d/%d" % (i + 1, len(files)), flush=True)

    cultures = sorted(set(r["culture"] for r in rows))
    pre_culture = np.full((len(cultures), len(LAGS)), np.nan)
    task_culture = np.full_like(pre_culture, np.nan)
    task_masked_culture = np.full_like(pre_culture, np.nan)
    culture_pre_rate = np.full(len(cultures), np.nan)
    for j, culture in enumerate(cultures):
        selected = [r for r in rows if r["culture"] == culture]
        pre_culture[j] = np.nanmean(np.stack([r["pre_ac"] for r in selected]), axis=0)
        task_culture[j] = np.nanmean(np.stack([r["task_ac"] for r in selected]), axis=0)
        task_masked_culture[j] = np.nanmean(np.stack([r["task_ac_masked"] for r in selected]), axis=0)
        culture_pre_rate[j] = np.mean([r["pre_rate"] for r in selected])

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    np.savez(args.out,
             files=np.array([r["path"] for r in rows]),
             cultures=np.array(cultures),
             duration=np.array([r["duration"] for r in rows]),
             pre_n=np.array([r["pre_n"] for r in rows]),
             pre_rate=np.array([r["pre_rate"] for r in rows]),
             pre_ac=np.stack([r["pre_ac"] for r in rows]),
             task_ac=np.stack([r["task_ac"] for r in rows]),
             task_ac_masked=np.stack([r["task_ac_masked"] for r in rows]),
             masked_fraction=np.array([r["masked_fraction"] for r in rows]),
             pre_culture=pre_culture,
             task_culture=task_culture,
             task_masked_culture=task_masked_culture,
             culture_pre_rate=culture_pre_rate,
             lags=LAGS * BIN_S)
    print("sessions", len(rows), "cultures", len(cultures))
    print("duration min/median/max", np.min([r["duration"] for r in rows]),
          np.median([r["duration"] for r in rows]), np.max([r["duration"] for r in rows]))
    print("pre spikes/session median", np.median([r["pre_n"] for r in rows]),
          "sessions >=20 spikes", sum(r["pre_n"] >= 20 for r in rows))
    print("saved", args.out)


if __name__ == "__main__":
    main()
