# VERIFICATION

This document lists every claim made in the paper and the brief, with the value, its source file and how to check it. It describes what is in this repository, how each claim can
be checked, and what its limits are. Nothing here asks the reader to change any file, analysis or manuscript.

## 1. What this repository is

The code and saved outputs of an independent, pre-registered re-analysis of DANDI 001611 (version 0.260611.0634),
taken at the analysis repository's tag `cp4` (2026-10-29). Two confirmatory questions were frozen before the held-out
run (tag `prereg-v1`, 2026-10-28 16:19 PDT; OSF registration osf.io/nxsph, 2026-10-28 19:51 PDT):

- **Q1 (first exposure):** in session 1 of each experiment, does activity in a 250-ms window just before trial n's own
  stimulation predict which of the two hidden sources will be stimulated? Statistic: ΔAUC = decoder AUC minus the mean
  of a 225-point circular-shift null, pooled over experiments nested in cultures.
- **Q2 (growth over 100 sessions):** does that prediction grow as the fixed sequence repeats? Statistic: ΔG, the growth
  of block AUC across 10 session blocks, against the same null.

Every number cited in the brief (`brief/at_a_glance.pdf`) is in `results.json`, each with its
source file and field.

## 2. Claims, with value, source and how to check

| # | Claim | Value | Source file (field) | How to check |
|---|---|---|---|---|
| C1 | Q1 pooled ΔAUC, 13 experiments in 9 cultures | +0.0034 (shown +0.003) | `results/D/heldout_primary/summary.json` (`Q1.PRIMARY.est`, `n_units`, `n_cultures`) | Open the JSON. Inverse-variance mean of `delta` in `forest_q1.csv` (weights 1/se²) is within 0.01 of it (the saved value is a REML multilevel fit) |
| C2 | Q1 95% CI | −0.0263 to +0.0332 | same (`Q1.PRIMARY.ci95`) | Open the JSON |
| C3 | Q1 randomization p | 0.727 (10,000 draws, 9,994 converged) | same (`randomization_p`, `randomization_n_converged`) | Open the JSON |
| C4 | Q1 equivalent at ±0.059 and at the secondary ±0.03 | true, true (TOST p 0.0013; 0.037) | same (`tost_equivalent`, `tost_secondary_0.03_equivalent`, `tost_p_tost`, `tost_secondary_0.03_p_tost`) | 90% CI (`ci90`) lies inside ±0.059 and inside ±0.03 (upper limit +0.0275: met narrowly) |
| C5 | Q1 outcome under the registered rule | A: bounded null | same (`Q1.PRIMARY.outcome`); rule in `docs/analysis_spec.md` section 7 | Compare the rule text with C2–C4 |
| C6 | Q2 pooled ΔG, 12 experiments in 8 cultures | +0.0036 (shown +0.004) | same (`Q2.PRIMARY.est`, `n_units`, `n_cultures`) | As C1, with `forest_q2.csv` |
| C7 | Q2 95% CI | −0.0063 to +0.0135 | same (`Q2.PRIMARY.ci95`) | Open the JSON |
| C8 | Q2 randomization p | 0.287 (9,989 converged) | same (`randomization_p`) | Open the JSON |
| C9 | Q2 equivalent at ±0.02 | true (TOST p 0.0029) | same (`tost_equivalent`) | `ci90` inside ±0.02 |
| C10 | Q2 outcome | A: bounded null | same (`Q2.PRIMARY.outcome`) | As C5 |
| C11 | Per-experiment Q1 and Q2 values in the forest plots | 13 and 12 rows | `results/D/heldout_primary/forest_q1.csv`, `forest_q2.csv` (`delta`, `se`); `units.csv` | `brief/b_q1_forest.csv` and `c_q2_forest.csv` are these rows plus the pooled row; CI = delta ± 1.96 se |
| C12 | Registered bounds (SESOI) | Q1 0.059, secondary 0.03; Q2 0.02 | `docs/preregistration_values.json` (`SESOI_Q1`, `SESOI_Q1_SECONDARY`, `SESOI_Q2`); echoed in `summary.json` `prereg` | Compare the two files; `docs/preregistration.md` gives the reasoning |
| C13 | The frozen files at run time equal tag `prereg-v1` | `changed_since_tag` = [], `uncommitted_in_frozen` = [] | `summary.json` (`provenance`) | `python check_hashes.py` recomputes every SHA-256 in this snapshot and compares |
| C14 | Split and lock file match the registered hashes | split 2d792f9e…, lock c8364adf… | `summary.json` (`provenance.split_sha256`, `lock_sha256`) vs `docs/preregistration_values.json` (`SPLIT_SHA256`, `LOCK_SHA256`) | `shasum -a 256 data/manifests/split.csv environment.lock.yml` |
| C15 | Both hard gates passed before the run | gate_a pass, gate_b pass | `results/B/B7/gates.json` | Open the JSON; `summary.json` `gates_sha256` is its hash |
| C16 | Timeline: tag 16:19:20, run 19:06:44–20:08:13, push 19:15, OSF 19:51, first output 19:58:46, first display 21:13:29 (PDT, 2026-10-28) | as listed | `brief/a_timeline.csv` (one source per row); `results/D/heldout_primary/run.log` first and last lines; the tag and push times come from the repository's git metadata, which is not in this snapshot | The run log lines are checkable here. The tag time is visible on request (`git for-each-ref refs/tags/prereg-v1`) and the OSF time on osf.io/nxsph once the embargo lifts |
| C17 | Injection sensitivity: Q1 effect found 80% of the time at ΔAUC 0.036 (same effect in every experiment, 9-culture design) or 0.063 (scaled to firing); Q2 at ΔG 0.013 or 0.050 | as listed | `results/B/B2/q1_homog_mde80.csv` (ho9), `q1_mde80.csv` (ho9, all, both), `q2_homog_mde80.csv`, `q2_mde80.csv` (all, both_ramp); curves in `*_power.csv` | Open the CSVs; `brief/d_detection_vs_effect.csv` is the plotted subset |
| C18 | The earlier analysis's "95% CI within 0.06 SD" corresponds to about ΔAUC 0.017 | 0.0169 | `tools/make_brief.py` (`EARLIER_BOUND`): Φ(0.06/√2) − 0.5, binormal AUC; the 0.06 SD bound is the one the earlier analysis reported | Recompute with scipy: `norm.cdf(0.06/2**0.5) - 0.5` |
| C19 | Why the earlier analysis's bound is narrower than our interval | it pools sessions as independent trials; our interval nests experiments in cultures and the 100 sessions of an experiment share one 256-trial sequence | Supplementary Information S2, item 1 (one 256-trial sequence per experiment, identical in all 100 sessions); check F4 of `tools/verify_earlier_findings.py` | Compare the `s` column of `/intervals/trials` across sessions of one experiment (the verification script does this for one experiment) |
| C20 | DANDI 001611: 2,700 files, 39.9 GB; held-out sessions about 22 GB | as listed | `data/manifests/d001611.assets.tsv` (`size`), `d001611_index.csv` + `split.csv` | Sum the `size` column |
| C21 | Pre-task and matched-task autocorrelation at a 1-s lag | −0.018 before task onset; +0.353 in matched task segments; 2,700 sessions, 12 cultures | `posthoc/output/summary.json` (`pretask`), `pretask_by_culture.csv` | Regenerate with `posthoc/pretask_cadence_audit.py`, then `summarize_controls.py` |
| C22 | Late response at 600-900 ms versus the evoked response at 100-200 ms | stimulated-minus-no-observation late difference: median 0.02 spikes/s/channel, range −0.25 to +0.64; median evoked rate 5.83 | `posthoc/output/summary.json` (`recovery`), `recovery_by_culture.csv` | Regenerate with `posthoc/response_recovery_depression.py`, then `summarize_controls.py` |
| C23 | Within-session response depression | second-half/first-half ratio: median 0.54, range 0.15-1.07; lower in 25 of 27 experiments | `posthoc/output/summary.json` (`within_session_response_depression`), `depression_by_experiment.csv` | As C22; ratios are computed within stimulus category before aggregation |

Values for the audit findings (the earlier, non-registered analysis of the same deposit) checked by `tools/verify_earlier_findings.py` (one volley per trial on a 1-s grid, the
3.45–3.10 s window sits before trial n−3, fixed sequences, (0,0) no-observation trials, artifact fractions, millisecond
timestamps, DIV) are in that script's header and in `tools/verify_earlier_findings_expected.txt`.

## 3. Run order and expected outputs

1. `python check_hashes.py` → every line `match`; last line `all frozen files match`.
2. `tools/verify_earlier_findings.py` (see README.md step 2) → 34 rows, all `OK`; runtime about 20 s to 3 min.
3. Full rerun (README.md step 3): environment, data (about 22 GB for the held-out split), then
   - dry run `--split dev --permuted` → `results/D/dev_permuted_primary/summary.json` with Q1 ΔAUC −0.005 (95% CI −0.030 to +0.021), Q2 ΔG −0.005 (−0.013 to +0.004), both outcome A (the included copy);
   - confirmatory run `--split heldout --i-have-cp2-signoff` → `results/D/heldout_primary/summary.json` with the values C1–C10 above. Randomization p-values use seeded draws and should reproduce exactly on the same library versions; REML estimates should agree to the printed precision.
   The guard needs a local git tag (README.md, "The guard"); the hash checks (2) and (3) of the guard pass on this repository as shipped.

## 4. Flags and limitations (all also reported in the paper's Supplementary Information)

- **Sensitivity rests on injected signals only.** The biological positive control (Q2) was itself null, and the
  closed-loop positive control (spec 8.7) could not be built because DANDI 001132 has no stimulation tables. The
  detection curves describe the pipeline, not a demonstrated capacity of the preparation.
- **Three held-out experiments are nearly blind to the Q1 injection** (C03_E01, C11_E03, C07_E01: injected ΔAUC at a 5%
  rate change of −0.004, +0.011, +0.027, under one null SD) and weakly sensitive for Q2. Each carries a pooled weight
  close to the others'. `results/D/heldout_primary/units.csv`, columns `q1_sens_dAUC`, `q2_sens_dG`.
- **The Q1 secondary bound (±0.03) is met narrowly:** 90% upper limit +0.0275.
- **Interpretation control flagged (spec 8.15):** growth for the target five trials ahead, s(n+5), had a held-out CI
  excluding 0 (+0.0105, randomization p 0.0025; Holm p 0.035 over the 14-test family). It was investigated under a plan
  registered before the investigation ran (deviation DV-1) and did not replicate on the development split (p 0.33), with
  no shared lag-5 structure in the sequences; under the pre-stated rules it is a chance finding. It is reported, not dropped.
- **Engine-timing control (spec 8.11) flags under its literal rule** ("any difference flags"): windows anchored on the
  recorded start_time instead of the 1-s grid change a few window counts; the AUC moves by at most 0.0027 (dev) and
  0.00065 (held-out), under 0.1 of a null SD. The difference is the known one-sample registration jitter of the
  start_time anchor; the grid anchor exists to remove it.
- **A property of the stimulation sequences, reported without interpretation:** source-1 labels 8 trials apart agree
  slightly more often than chance across the 27 sequences (+0.037; p 0.0008 centered, Holm 0.038 over 48 tests;
  uncentered Holm 0.20). Not followed up; listed for the follow-up paper.
- **External timestamps came after the run started.** The GitHub push (19:15) and the OSF registration (19:51) came
  after the held-out run started (19:06) but before it ended (20:08) and before any result was displayed (21:13). The
  pre-run freeze evidence is the git tag (16:19), verified at run time by the guard. The registration is pre-analysis
  for this pipeline on the held-out split, not pre-data: the recordings are public and had been analyzed before this plan was frozen.
- **Three inputs were not hashed by the guard:** `results/B/B1/div_check.csv`, `data/manifests/d001611_index.csv` and
  `results/B/B1/units.csv`. They are included here; their SHA-256 values were recorded in the analysis repository on 29 October 2026, and PROVENANCE.md section 4 lists their blob IDs.
- **Controls 8.2, 8.3 and 8.11 were run after the primary analysis** (the pre-registration fixed no timing); 8.8 (raster
  review) was not applicable because no effect was found.
- **The OSF registration is embargoed** during peer review and is made public at acceptance.
- **The guard needs a local git tag** `prereg-v1`, which this repository's history does not carry (see README.md). `check_hashes.py` is the provenance check.
- **What this is not:** a claim about the preparation in general, about other datasets, or about the earlier analysis
  beyond the data findings summarized in Supplementary Information S2. Statements are limited to this dataset and this pipeline.
- **Post-hoc controls (C21-C23) are descriptive, not part of the registered Q1/Q2 tests.** The fixed 1-s design can
  show whether late activity resembles no-observation trials and whether the response declines within a session; it
  cannot identify a recovery time constant or separate adaptation from other causes of depression. See `posthoc/README.md`.
