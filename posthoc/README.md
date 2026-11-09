# Post-hoc internal controls

These scripts reproduce the descriptive controls added after the registered Q1/Q2 run. They do not change any registered result and are not part of the frozen, hash-pinned pipeline.

## Analyses

- `pretask_cadence_audit.py`: compares population-spike autocorrelation before the first trial with an equally long task segment. The task segment is a positive control for resolving the 1-s rhythm in a short recording.
- `response_recovery_depression.py`: measures evoked activity at 100-200 ms, late activity at 600-900 ms, and the second-half/first-half evoked-response ratio within each session. No-observation trials provide the late-activity comparison.
- `summarize_controls.py`: writes the culture- and experiment-level CSV files and `summary.json` from the two NPZ files.

The fixed 1-s design can measure late residual activity and within-session response depression. It cannot identify a recovery time constant or distinguish adaptation from other causes of depression.

## Run

Run from the repository root after downloading DANDI 001611 as described in the main README:

```bash
python posthoc/pretask_cadence_audit.py
python posthoc/response_recovery_depression.py
python posthoc/summarize_controls.py
```

Defaults read `data/raw/d001611/` and write `posthoc/output/`. Use `--data-dir`, `--out`, or `--out-dir` to change these locations. `--stride` and `--max-files` on the two analysis scripts support small smoke tests.

The included `output/summary.json` and CSV files are the values reported in the manuscript. The NPZ intermediates are regenerable from the public recordings and are not committed.
