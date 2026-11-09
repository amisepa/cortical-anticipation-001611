# Copyright 2026 Cedric Cannard and William Reid
# SPDX-License-Identifier: GPL-3.0-or-later
"""Summarize the two post-hoc internal-control analyses as JSON and CSV files."""
import argparse
import csv
import json
import os

import numpy as np


def culture_from_filename(path):
    for part in str(path).replace('\\', '/').split('/'):
        if part.startswith('sub-') and part.endswith('_dl'):
            return part[:-3].split('_')[0]
    raise ValueError('No culture folder in ' + str(path))


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pretask', default='posthoc/output/pretask_cadence_all.npz')
parser.add_argument('--response', default='posthoc/output/response_recovery_all.npz')
parser.add_argument('--out-dir', default='posthoc/output')
args = parser.parse_args()
os.makedirs(args.out_dir, exist_ok=True)

pre = np.load(args.pretask)
i1 = int(np.argmin(np.abs(pre['lags'] - 1.0)))
pre_1s = pre['pre_culture'][:, i1]
task_1s = pre['task_culture'][:, i1]
with open(os.path.join(args.out_dir, 'pretask_by_culture.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['culture', 'pretask_autocorrelation_1s', 'task_autocorrelation_1s'])
    for culture, a, b in zip(pre['cultures'], pre_1s, task_1s):
        w.writerow([culture, float(a), float(b)])

res = np.load(args.response)
files = res['files']
file_cultures = np.array([culture_from_filename(f) for f in files])
cultures = sorted(set(file_cultures))
recovery_rows = []
for culture in cultures:
    selected = file_cultures == culture
    stim = res['curve_stim'][selected].mean(axis=0)
    blank = res['curve_blank'][selected].mean(axis=0)
    early = stim[2:4].mean()
    late = stim[12:18].mean()
    late_blank = blank[12:18].mean()
    difference = late - late_blank
    recovery_rows.append([culture, early, late, late_blank, difference, difference / early])
with open(os.path.join(args.out_dir, 'recovery_by_culture.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['culture', 'evoked_100_200_hz_per_channel', 'late_600_900_hz_per_channel',
                'no_observation_late_hz_per_channel', 'late_difference', 'difference_over_evoked'])
    w.writerows(recovery_rows)

responses = res['response']
depression_rows = []
for culture in cultures:
    idx = np.where(file_cultures == culture)[0]
    assert len(idx) % 100 == 0
    for start in range(0, len(idx), 100):
        block = idx[start:start + 100]
        early = np.nanmean(responses[block[:10]], axis=0)
        late = np.nanmean(responses[block[-10:]], axis=0)
        valid = np.array([False, True, True, True]) & (early[:, 0] > 0) & (early[:, 1] > 0) & (late[:, 0] > 0) & (late[:, 1] > 0)
        within = responses[block]
        within_ratio = np.exp(np.nanmean(np.log(within[:, valid, 1] / within[:, valid, 0])))
        depression_rows.append([culture, start // 100 + 1, within_ratio])
with open(os.path.join(args.out_dir, 'depression_by_experiment.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['culture', 'experiment_within_culture', 'second_half_over_first_half'])
    w.writerows(depression_rows)

ratios = np.array([r[2] for r in depression_rows])
differences = np.array([r[4] for r in recovery_rows])
evoked = np.array([r[1] for r in recovery_rows])
summary = {
    'analysis_status': 'post-hoc descriptive controls; not part of the registered Q1/Q2 tests',
    'pretask': {
        'sessions': int(len(pre['files'])), 'cultures': int(len(pre['cultures'])),
        'duration_seconds_median': float(np.median(pre['duration'])),
        'duration_seconds_range': [float(pre['duration'].min()), float(pre['duration'].max())],
        'pretask_spikes_per_session_median': float(np.median(pre['pre_n'])),
        'sessions_with_at_least_20_pretask_spikes': int((pre['pre_n'] >= 20).sum()),
        'autocorrelation_1s_pretask_culture_mean': float(np.nanmean(pre_1s)),
        'autocorrelation_1s_task_culture_mean': float(np.nanmean(task_1s)),
    },
    'recovery': {
        'cultures': len(recovery_rows),
        'late_stimulated_minus_no_observation_hz_per_channel_median': float(np.median(differences)),
        'late_difference_range': [float(differences.min()), float(differences.max())],
        'evoked_100_200_hz_per_channel_median': float(np.median(evoked)),
    },
    'within_session_response_depression': {
        'experiments': len(depression_rows),
        'second_half_over_first_half_median': float(np.median(ratios)),
        'ratio_range': [float(ratios.min()), float(ratios.max())],
        'experiments_with_second_half_lower': int((ratios < 1).sum()),
    },
}
with open(os.path.join(args.out_dir, 'summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)
    f.write('\n')
print(json.dumps(summary, indent=2))
