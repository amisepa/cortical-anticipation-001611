# Copyright 2026 Cedric Cannard and William Reid
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare population-spike autocorrelation before and after task onset.

For each session, the pre-task interval [0, first trial) is compared with an equally
long interval beginning at the first trial. The task interval is a positive control:
it contains the known once-per-second events. Population spikes are binned at 10 ms.
Normalized autocorrelations are calculated at lags 0.10-2.00 s and averaged by culture.
"""
import argparse
import glob
import os

import h5py
import numpy as np

BIN_S = 0.01
LAGS = np.arange(10, 201)


def autocorrelation(counts):
    """Normalized autocovariance with overlap-length correction."""
    x = counts.astype(np.float64) - counts.mean()
    var = np.mean(x * x)
    if not np.isfinite(var) or var == 0:
        return np.full(len(LAGS), np.nan)
    return np.array([np.mean(x[:-lag] * x[lag:]) / var for lag in LAGS])


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir', default='data/raw/d001611')
parser.add_argument('--out', default='posthoc/output/pretask_cadence_all.npz')
parser.add_argument('--stride', type=int, default=1)
parser.add_argument('--max-files', type=int)
args = parser.parse_args()

files = sorted(glob.glob(os.path.join(args.data_dir, 'sub-*_dl', '*.nwb')))[::args.stride]
if args.max_files is not None:
    files = files[:args.max_files]
if not files:
    raise RuntimeError('No NWB files found under ' + args.data_dir)

rows = []
for i, path in enumerate(files):
    culture = os.path.basename(os.path.dirname(os.path.dirname(path))).split('_')[0]
    with h5py.File(path, 'r') as f:
        spikes = np.asarray(f['units/spike_times'], dtype=np.float64) / 1000.0
        first = float(f['intervals/trials/start_time'][0]) / 1000.0
        n_units = len(f['units/id'])
    duration = np.floor(first / BIN_S) * BIN_S
    edges = np.arange(0, duration + BIN_S / 2, BIN_S)
    pre = spikes[(spikes >= 0) & (spikes < duration)]
    task = spikes[(spikes >= duration) & (spikes < 2 * duration)] - duration
    pre_ac = autocorrelation(np.histogram(pre, bins=edges)[0])
    task_ac = autocorrelation(np.histogram(task, bins=edges)[0])
    rows.append((culture, path, duration, n_units, len(pre), len(pre) / duration / n_units,
                 len(task), pre_ac, task_ac))
    if (i + 1) % 100 == 0 or i + 1 == len(files):
        print('%d/%d' % (i + 1, len(files)), flush=True)

cultures = sorted(set(r[0] for r in rows))
pre_culture = np.full((len(cultures), len(LAGS)), np.nan)
task_culture = np.full_like(pre_culture, np.nan)
pre_rate = np.full(len(cultures), np.nan)
for j, culture in enumerate(cultures):
    selected = [r for r in rows if r[0] == culture]
    pre_culture[j] = np.nanmean(np.stack([r[7] for r in selected]), axis=0)
    task_culture[j] = np.nanmean(np.stack([r[8] for r in selected]), axis=0)
    pre_rate[j] = np.mean([r[5] for r in selected])

os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
np.savez(args.out, files=np.array([r[1] for r in rows]), cultures=np.array(cultures),
         duration=np.array([r[2] for r in rows]), pre_n=np.array([r[4] for r in rows]),
         pre_rate=np.array([r[5] for r in rows]), pre_ac=np.stack([r[7] for r in rows]),
         task_ac=np.stack([r[8] for r in rows]), pre_culture=pre_culture,
         task_culture=task_culture, culture_pre_rate=pre_rate, lags=LAGS * BIN_S)
print('sessions', len(rows), 'cultures', len(cultures))
print('duration min/median/max', np.min([r[2] for r in rows]), np.median([r[2] for r in rows]),
      np.max([r[2] for r in rows]))
print('pre spikes/session median', np.median([r[4] for r in rows]),
      'sessions >=20 spikes', sum(r[4] >= 20 for r in rows))
print('saved', args.out)
