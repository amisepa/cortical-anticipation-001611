# Copyright 2026 Cedric Cannard and William Reid
# SPDX-License-Identifier: GPL-3.0-or-later
"""Measure post-volley recovery and within-session response depression in DANDI 001611.

Deposited times are milliseconds. The trial registration time is the volley time.
Evoked responses are measured 100-300 ms after that time, excluding the early artifact.
Residual late activity is measured at 600-900 ms. Stimulated trials are compared with
(0,0) no-observation trials. Response depression is measured within category and session.
"""
import argparse
import glob
import os

import h5py
import numpy as np

BINS = np.arange(0, 1001, 50, dtype=float)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir', default='data/raw/d001611')
parser.add_argument('--out', default='posthoc/output/response_recovery_all.npz')
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
        spikes = np.sort(np.asarray(f['units/spike_times'], dtype=np.float64))
        starts = np.asarray(f['intervals/trials/start_time'], dtype=np.float64)
        obs = np.asarray(f['intervals/trials/o'])
        sources = np.asarray(f['intervals/trials/s'])
        n_units = len(f['units/id'])
    categories = sources[:, 0].astype(int) + 2 * sources[:, 1].astype(int)
    stimulated = np.any(obs != 0, axis=1)
    response = np.full((4, 2), np.nan)
    for cat in range(4):
        for half, mask_half in enumerate((np.arange(256) < 128, np.arange(256) >= 128)):
            selected = starts[(categories == cat) & mask_half]
            counts = np.searchsorted(spikes, selected + 300) - np.searchsorted(spikes, selected + 100)
            if len(counts):
                response[cat, half] = counts.sum() / len(counts) / n_units
    curve_stim = np.zeros(20)
    curve_blank = np.zeros(20)
    for t0, is_stim in zip(starts, stimulated):
        lo, hi = np.searchsorted(spikes, t0), np.searchsorted(spikes, t0 + 1000)
        h = np.histogram(spikes[lo:hi] - t0, bins=BINS)[0]
        if is_stim:
            curve_stim += h
        else:
            curve_blank += h
    ns, nb = int(stimulated.sum()), int((~stimulated).sum())
    curve_stim /= max(ns, 1) * n_units * 0.05
    curve_blank /= max(nb, 1) * n_units * 0.05
    rows.append((culture, path, response, curve_stim, curve_blank, ns, nb))
    if (i + 1) % 100 == 0 or i + 1 == len(files):
        print('%d/%d' % (i + 1, len(files)), flush=True)

cultures = sorted(set(r[0] for r in rows))
os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
np.savez(args.out, files=np.array([r[1] for r in rows]), cultures=np.array(cultures),
         response=np.stack([r[2] for r in rows]), curve_stim=np.stack([r[3] for r in rows]),
         curve_blank=np.stack([r[4] for r in rows]), n_stim=np.array([r[5] for r in rows]),
         n_blank=np.array([r[6] for r in rows]))

responses = np.stack([r[2] for r in rows])
file_cultures = np.array([r[0] for r in rows])
experiment_rows = []
complete_experiments = all(np.sum(file_cultures == culture) % 100 == 0 for culture in cultures)
for culture in cultures if complete_experiments else []:
    idx = np.where(file_cultures == culture)[0]
    for start in range(0, len(idx), 100):
        block = idx[start:start + 100]
        early = np.nanmean(responses[block[:10]], axis=0)
        late = np.nanmean(responses[block[-10:]], axis=0)
        valid = np.array([False, True, True, True]) & (early[:, 0] > 0) & (early[:, 1] > 0) & (late[:, 0] > 0) & (late[:, 1] > 0)
        session_ratio = np.exp(np.mean(np.log(late[valid, 0] / early[valid, 0])))
        within = responses[block]
        within_ratio = np.exp(np.nanmean(np.log(within[:, valid, 1] / within[:, valid, 0])))
        experiment_rows.append((culture, start // 100 + 1, session_ratio, within_ratio))
print('experiments', len(experiment_rows))
if experiment_rows:
    print('within-session late/early median %.3f range %.3f-%.3f; decreased %d/%d' %
          (np.median([r[3] for r in experiment_rows]), min(r[3] for r in experiment_rows),
           max(r[3] for r in experiment_rows), sum(r[3] < 1 for r in experiment_rows),
           len(experiment_rows)))
print('saved', args.out)
