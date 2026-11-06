# Can rat cortical cultures predict what comes next, unpredictable or learned?

**Re-analysis code for the confirmatory study of DANDI dataset 001611 (questions Q1 and Q2).**

Cedric Cannard (Swartz Center for Computational Neuroscience, UC San Diego; Valis Corporation, Encinitas, CA, USA) and Will Reid (Valis Corporation, Encinitas, CA, USA).

The accompanying manuscript is under submission. This repository contains the analysis code, the frozen pre-analysis plan, the split and session manifests, the saved outputs of the confirmatory run, the figures, and a verification script. **It contains no recordings.** Nothing in it needs to be run to read the results. `VERIFICATION.md` lists every claim in the paper with its source file and how to check it.

## What is here

| Folder / file | What it is |
|---|---|
| `VERIFICATION.md` | Every claim (value, source file, how to check), the run order with expected outputs, all flags and limitations |
| `results.json` | Every cited number, each with its source file and field |
| `src/organoid_anticipation/` | The pipeline (reader, windows, decoder, nulls, pooling in R via rpy2, synthetic injection). Frozen at tag `prereg-v1` |
| `scripts/D_confirmatory.py` | The single confirmatory run (Q1, Q2, sensitivities, controls, forest plots). Frozen |
| `scripts/B1_build_experiments.py` | Builds one unit (experiment) from its session files. Frozen |
| `scripts/A2_split.py`, `scripts/B0_download_001611.py` | How the development / held-out split was drawn (seeded) and how the files were downloaded and hash-verified |
| `tools/verify_earlier_findings.py`, `..._expected.txt` | Standalone check of the audit of the earlier, non-registered analysis of the same deposit: streams one session from DANDI, about 20 s to 3 min |
| `tools/make_brief.py` | Builds the four figures, the two-page brief and `results.json` from the saved outputs only |
| `docs/preregistration.md`, `docs/preregistration_values.json`, `docs/analysis_spec.md` | The frozen pre-registration and analysis specification (spec v0.4); their SHA-256 values are in the OSF registration (osf.io/nxsph) |
| `data/manifests/` | `split.csv` (dev / held-out assignment; SHA-256 in the pre-registration), `d001611_index.csv` (every session: path, size, SHA-256), the DANDI asset list (path, size, SHA-256) and the download provenance |
| `results/B/B1/` | `units.csv` (one row per unit), `div_check.csv` (culture age) |
| `results/B/B2/` | Injection power tables (development split, permuted labels; behind figure d) |
| `results/B/B7/` | The two hard gates (`gates.json`) that had to pass before the held-out run |
| `results/D/heldout_primary/` | **The confirmatory run:** `summary.json` (pooled results, provenance and file hashes), `units.csv` (per experiment), `forest_q1/q2.csv/.png`, `nulls.npz`, `run.log` |
| `results/D/heldout_L360/` | The pre-registered 360-ms window sensitivity run |
| `results/D/dev_permuted_primary/` | The dry run on the development split with permuted labels (what the dry-run command below reproduces) |
| `brief/` | The two-page brief (`at_a_glance.pdf`) and its figures, each with its data as CSV; `pdf_text.txt` is the brief as plain text |
| `tests/` | Unit tests (`pytest -q`) |
| `environment.yml`, `environment.lock.yml` | Conda environment. The lock file is the registered one, byte for byte (its last line is the authoring machine's conda `prefix:`; conda ignores it on another machine) |
| `check_hashes.py` | Compares every frozen file in this repository with the SHA-256 recorded in `results/D/heldout_primary/summary.json` |

## Reading the results without running anything

- `results.json`: the cited numbers with sources.
- `results/D/heldout_primary/summary.json` → `Q1.PRIMARY` and `Q2.PRIMARY`: estimate, 95% and 90% CI, randomization p, TOST, Bayes factor, outcome.
- `results/D/heldout_primary/units.csv`: one row per held-out experiment, with its AUC, shift-null mean and SD, growth G, injected sensitivity.
- `brief/at_a_glance.pdf`: the two-page summary.

## Run order

1. **Hash check (seconds, no environment needed):** `python check_hashes.py`. Expected: every frozen file, `split.csv` and `gates.json` report `match`, and the last line reads `all frozen files match`.
2. **Verification script (about 20 s to 3 min, streams about 20 MB from DANDI):**
   ```bash
   python -m venv venv && venv/bin/pip install numpy h5py remfile      # Windows (Git Bash): venv/Scripts/pip, venv/Scripts/python
   venv/bin/python tools/verify_earlier_findings.py > my_output.txt
   diff my_output.txt tools/verify_earlier_findings_expected.txt
   ```
   Expected: 34 rows, every row `OK`; per-experiment values may differ slightly from the expected file, which the header explains.
3. **Full rerun (environment, data, then the two commands below).**

### 3a. Environment (both platforms)

```bash
conda env create -f environment.yml
conda activate organoid-anticipation
pytest -q
```

R (metafor, lme4) is installed by conda as part of the environment; the pooling step calls it through rpy2.
On Windows use Git Bash (or the Anaconda prompt for the `conda` lines) and run everything from the folder that holds this README.

### 3b. Data: DANDI 001611, version 0.260611.0634

- Dandiset: https://dandiarchive.org/dandiset/001611/0.260611.0634 (DOI 10.48324/dandi.001611/0.260611.0634, CC-BY-4.0).
- 2,700 spikes-only NWB files, 39.9 GB in total. The held-out split alone (the 1,500 sessions of the held-out experiments) is about 22 GB; the development split about 18 GB.
- On our connection the full 40 GB took about 75 minutes (roughly 9 MB/s). Allow 30–90 minutes for the held-out half, depending on your connection.
- `scripts/B0_download_001611.py` downloads every file and verifies each SHA-256 against the DANDI asset checksum:

```bash
python -I scripts/B0_download_001611.py 8        # 8 parallel workers; files go to data/raw/d001611/
```

  To download only the held-out sessions, filter `data/manifests/d001611_index.csv` by the experiments marked `heldout` in `data/manifests/split.csv` and fetch those paths with the DANDI CLI (`dandi download` accepts asset URLs), then let `B1_build_experiments.py` verify the hashes.

- Split check: `shasum -a 256 data/manifests/split.csv` (Mac) or `sha256sum data/manifests/split.csv` (Git Bash) must print `2d792f9ebc1fdf3a82f83c709a0c40ef6417c357dc5799fe40100715b9e65ef9`, the value in `docs/preregistration_values.json`.

### 3c. Dry run (development split, permuted labels; no guard)

```bash
python -I scripts/D_confirmatory.py --split dev --permuted --n-jobs 6
```

Writes `results/D/dev_permuted_primary/` (about 45 minutes on 6 cores). Compare `summary.json` with the copy included here.

### 3d. The confirmatory run (held-out split, real labels)

```bash
git tag prereg-v1      # once, in your clone; see "The guard"
python -I scripts/D_confirmatory.py --split heldout --i-have-cp2-signoff --n-jobs 12
```

About 62 minutes on 12 cores. Writes `results/D/heldout_primary/`; expected values are in `VERIFICATION.md` and in the included `summary.json`. For the 360-ms sensitivity add `--sensitivity L360`.

**The guard.** Before it runs on held-out data, the script refuses unless (1) a git tag `prereg-v1` exists and every frozen file is identical to it, with no uncommitted changes, (2) `split.csv` and `environment.lock.yml` match the SHA-256 values in `docs/preregistration_values.json`, and (3) both gates in `results/B/B7/gates.json` passed. Checks (2) and (3) compare against the registered values and pass on this repository as shipped. Check (1) needs a git tag `prereg-v1`; this repository's history starts at the public release and does not carry the original tag, so the `git tag` line above creates it locally, and what that check then guarantees is only that you have not edited the frozen files since tagging. The check that matters for provenance is `check_hashes.py`, which compares every frozen file with the hashes the original run recorded; the hashes of the three plan documents are also in the OSF registration.

### 4. The brief figures

```bash
python tools/make_brief.py          # reads results/D and results/B/B2; writes brief/ and results.json
```

## Data

All data are public: the main dataset is DANDI 001611 (version 0.260611.0634, DOI 10.48324/dandi.001611/0.260611.0634, CC-BY-4.0), the hidden-source inference experiments of Mayama et al. (arXiv:2510.04084). Calibration datasets used in the paper: DANDI 001336, 001850, 001374 and 001872. Download and hash-verification: `scripts/B0_download_001611.py`.

## License

Code: GPL-3.0 (see LICENSE). Copyright 2026 Cedric Cannard and Will Reid. The registered plan text and figures are CC-BY-4.0.

## How to cite

Cannard, C. & Reid, W. (2026). Can rat cortical cultures predict what comes next, unpredictable or learned? Manuscript under submission. Code: https://github.com/amisepa/cortical-anticipation-001611

## References

- Mayama, T., Shimizu, S., Takano, Y., Akita, D. & Takahashi, H. (2026). Spiking data of dissociated rat cortical cultures on HD-MEAs during repeated-stimulation experiment (Version 0.260611.0634) [Data set]. DANDI Archive. https://doi.org/10.48324/dandi.001611/0.260611.0634
- Mayama, T., Akita, D., Shimizu, S., Takano, Y. & Takahashi, H. (2026). Bridging integrated information theory and the free-energy principle in living neuronal networks. arXiv:2510.04084. The paper that describes the experiments in DANDI 001611.
- Viechtbauer, W. (2010). Conducting meta-analyses in R with the metafor package. *Journal of Statistical Software*, 36(3), 1–48. https://doi.org/10.18637/jss.v036.i03. Used for pooling (`rma.mv`, REML, experiments nested in cultures).
- Lakens, D. (2017). Equivalence tests: a practical primer for t tests, correlations, and meta-analyses. *Social Psychological and Personality Science*, 8(4), 355–362. https://doi.org/10.1177/1948550617697177. Used for the TOST equivalence tests.
- Pedregosa, F. et al. (2011). Scikit-learn: machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830. Used for the decoders and AUC.

## Integrity

`python check_hashes.py` compares each frozen file in this repository with the SHA-256 of the frozen files recorded in
`results/D/heldout_primary/summary.json` (`provenance.file_sha256`), written by the run itself. Every file should
report `match`. The same hashes for the three pre-registration documents are in the OSF registration summary (osf.io/nxsph).

## Seeds

Global seed 20261026; every per-task seed is derived from it by name (`organoid_anticipation.derive_seed`) and recorded in the outputs.
