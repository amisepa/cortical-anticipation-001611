# Preregistration: Content Anticipation in In-Vitro Neural Preparations (DANDI 001611)

**Status: FROZEN** at tag `prereg-v1` (CP2, 2026-10-28; PI sign-off `docs/checkpoints/CP2.md`, decisions `docs/checkpoints/CP2_decisions_message.md`). Nothing here, in `docs/preregistration_values.json` or in `docs/analysis_spec.md` (v0.4) may change after that tag. Later changes go in "Deviations" below and are labeled exploratory.

**Author:** Will Reid | **Spec:** `docs/analysis_spec.md` v0.4 | **Decisions:** `docs/decisions_log.md` (D-001 to D-067) | **OSF:** not posted

## 1. Hypotheses

- **Q1 (primary; the paper's question).** In session 1 of each experiment (first exposure to its 256-trial sequence), does activity before any stimulation on trial n carry information about the hidden sources s¹(n), s²(n), beyond trial history? H0₁: conditional independence given H(n). Two-sided.
- **Q2 (secondary confirmatory; learned expectation and biological positive control).** Across the 100 sessions of an experiment, does history-residualized pre-stimulus decodability grow? H0₂: no change. Two-sided; expected sign positive.

A positive Q1 result is first attributed to engine/RNG leakage, closed-loop causation, analysis artifact, carryover combined with chance sequence structure, or chance (spec 1b). A positive Q2 result is ordinary learned expectation, never evidence of anomalous anticipation.

## 2. Data

- **Dataset:** DANDI 001611 version 0.260611.0634; 2,700 NWB files, all sha256-verified (`data/manifests/provenance/d001611_bulk.csv`). 12 rat (E18) dissociated cortical cultures, MaxOne-geometry HD-MEA, 27 experiments × 100 sessions × 256 trials.
- **Held-out split:** `data/manifests/split.csv`, SHA-256 `2d792f9ebc1fdf3a82f83c709a0c40ef6417c357dc5799fe40100715b9e65ef9`, created before any outcome analysis (D-026).
- **Who has seen held-out outcomes:** nobody. Held-out data have been used only for:
  - label-free integrity checks: timestamps, volleys, fingerprints, metadata, and the stimulation-free check of the fixed window;
  - labels-only sequence checks: identity across sessions, no reuse across experiments, and the position-level randomness audit (gate b).
- **Confirmatory sets (D-041, D-067):**
  - **Q1:** session 1 of the 12 held-out experiments of multi-experiment cultures plus C02 (whose held-out half contains session 1): **13 experiments in 9 cultures**. None is excluded for its response window (D-059).
  - **Q2:** the 12 held-out experiments of multi-experiment cultures, **12 experiments in 8 cultures**. Single-experiment cultures are descriptive only.
  - **Age:** five Q1 experiments are younger than DIV 15 at session 1 (C01_E02, C04_E01, C05_E02, C07_E01, C09_E01; age from recording dates, D-056). The age sensitivity therefore has 8 experiments in 6 cultures for Q1 and 7 in 5 for Q2.
- **Inclusion (spec 3):** sessions with 256 trials, monotonic times, catch count = volley-free count, and spike count ≥ 1% of the experiment median. A trial is dropped if its window overlaps any detected volley's blanking span (D-060; 1 of 691,200 trials, in a session no confirmatory analysis uses).

## 3. Definitions (spec 2, 12)

| Parameter | Value | Decisions-log ID |
|---|---|---|
| Targets | Two binary decoders, s¹ and s² | D-037 |
| t₀ | Per-session Theil–Sen 1-s engine grid + the experiment's median detected volley onset offset, all trials | D-002b, D-005b |
| Volley detection | ≥ 3 bins of 0.25 ms with ≥ 10% of channels detecting, within [start − 16 ms, start + 12 ms] | D-029, D-051, D-052 |
| **Pre-stimulus window** | **[t₀ − 265 ms, t₀ − 15 ms] (250 ms) for every experiment**: stimulation-free, carryover residualized. No response-window exclusion; response windows and decay curves are descriptive (8.13); label-free carryover ratio reported per experiment | D-059, D-060 |
| Artifact blanking | Volley onset − 4 ms to offset + 3 ms (post-stimulus checks only) | D-007b |
| Channels | ≥ 0.01 Hz in the windows over the experiment (label-free) | CP1 |
| Count transform | log1p; ranks as sensitivity | D-044 |

## 4. Primary analyses

**Q1 (per experiment, session 1, positions 2–255):**
- **Features:** log1p total window count, and log1p counts in spatial pools A (≤ 100 µm from an o-bit 1–16 electrode), B (bits 17–32) and C (others) (D-039).
- **History H(n), 11 columns:** s(n−1), s(n−2), o(n−1) half counts, log1p r(n−1) total and pools (25–300 ms after t₀(n−1); spontaneous counts on no-observation trials, D-067), and position. Cross-fitted ridge residualization (α = 1) inside training folds.
- **Decoder:** L2 logistic regression, C = 1, on standardized residualized features.
- **CV:** 5 contiguous position blocks with a 5-position gap.
- **Statistic:** mean over the two sources of the mean within-fold AUC.

**Q2 (per experiment, 100 sessions):**
- **Features:** log1p per-channel window counts.
- **H(n):** Q1's columns plus session index, previous-session mean window rate, cumulative pulses, s frequencies over the last 10/50 trials, and 5 in-fold PCs of per-channel r(n−1).
- **Decoder:** L2 logistic, **C = 0.01** (D-053; plateau from 10⁻⁴ to 10⁻², D-053b).
- **CV:** 10 blocks of 10 sessions, with position-aligned 5-block CV within each block.
- **Statistic:** **G = 9 × OLS slope of block AUC on block index** (D-040, approved at CP2). Secondary: block 10 (sessions 91–100) − block 1 (sessions 1–10).

**Uncertainty (both):**
- **Sequence-shift null:** every shift k ∈ [16, 240] once (225), the same k in every session, history unshifted (D-062). ΔAUC_e (or ΔG_e) = statistic − null mean; v_e = null variance.
- **Pooling:** metafor `rma.mv` (REML, random = ~1 | culture/experiment, t-test, df = cultures − 1).
- **Primary p-value:** randomization test, drawing one shift-null value per experiment and refitting the REML model, 10,000 draws (D-064).

**Entry point:** `python -I scripts/D_confirmatory.py --split heldout --i-have-cp2-signoff`, run from a checkout whose frozen files equal tag `prereg-v1`. The script refuses otherwise; it also checks the split and lock-file hashes and that both gates passed, and writes commit, tag and file hashes into `summary.json`.

## 5. Decision rules (spec 7; D-064)

**Q1.**
- **SESOI_Q1 = ΔAUC 0.059**, the conversion of the human presentiment effect (d ≈ 0.21). It is fixed regardless of the held-out N.
- The realized **90% CI** is reported as the achieved bound.
- **Secondary (labeled):** TOST at ±0.03.

**Q2.** **SESOI_Q2 = 0.02** (growth from block 1 to block 10, ΔAUC units).

**Both questions:**
- **Equivalence:** TOST at ±SESOI, α = 0.05.
- **Bayes factor:** BF10 with a Cauchy(0, SESOI) prior; robustness at 0.5× and 2×.
- **Outcomes:**
  - **B, candidate effect:** the 95% CI excludes 0, **and** the randomization p < 0.05, **and** every Section 8 control passes, whatever the size relative to SESOI. Size relative to SESOI is reported. *Requiring both the CI and the primary p-value is our reading of the CP2 decision; disagreement is flagged in `summary.json`.*
  - **A, bounded null:** not B, and equivalence at ±SESOI.
  - **C, inconclusive:** neither. Report the CI and the achieved bound.

## 6. Required controls and pass criteria (spec 8)

**Hard gates, run on the dev split before the held-out run (8.14; D-061; criteria committed at a163d6a before running). Both PASS** (`results/B/B7/gates.json`):

| Gate | Criterion | Result |
|---|---|---|
| (a) residualized W(n) cannot decode s(n−1), real dev labels, reference = permuted label worlds | 95% CI upper < 0.03 (Q1) / 0.02 (Q2), lower ≤ 0 | Q1: excess +0.002 (−0.012 to +0.016), 14 units / 11 cultures. Q2: +0.0005 (−0.004 to +0.005), 11 / 8. **PASS.** Unresidualized windows do carry s(n−1) (mean AUC 0.545 Q1, 0.581 Q2, vs 0.50) |
| (b) position-level randomness audit, all 27 sequences | No rejection after Holm (27 × 16 tests) or Bonferroni (18 global tests); (0,0) ⇔ no bits exact | Min Holm p 0.80; min global Bonferroni p 0.24; 0 structural mismatches; every experiment one sequence in all sessions; no cross-experiment reuse (max shifted/swapped agreement 0.60). **PASS** |

**Other controls:**
- **8.1/8.10 injection and power** (`results/B/B2/`; below).
- **8.2** post-stimulus decoding and off-by-one (`results/B/B3/8_2_*`): peak at lag 0 in all 15 dev units.
- **4.2** catch/volley and o-column mapping (`results/B/B3/4_2*`).
- **8.3/8.5/8.11/8.12** code paths on permuted labels (`results/B/B4/`).
- **8.13** descriptive decay and carryover (`results/B/B3/8_13_*`).
- **8.15 Q2 interpretation controls** (D-065):
  - per-block unresidualized AUC for s(n−1);
  - growth for s(n+5) and s(n+10), flagged if either pooled 95% CI excludes 0 (investigate, not automatically an artifact);
  - the Q2 swap null.
- **8.7** closed-loop positive control: **not available** (001132 has no stimulation tables; D-050).

**Per-experiment injected sensitivity** (Q1: δ = 0.05 on all included channels; Q2: ramp to δ = 0.1) is computed in the confirmatory run and shown next to each forest plot (D-063).

## 7. Power at the realized design (dev split, permuted labels; `results/B/B2/`)

| | Q1, all 14 dev units (11 cultures) | Q1, 9 cultures (held-out-like) | Q2, 11 dev units (8 cultures) |
|---|---|---|---|
| 80% detection, homogeneous effect | ΔAUC 0.031 | 0.036 | ΔG 0.013 |
| 80% detection, rate-proportional injection on all channels | 0.054 | 0.063 | 0.050 |
| 80% detection, injection on pools A+B / top-8 channels | 0.049 / 0.074 | 0.060 / 0.088 | 0.080 / 0.090 |
| Detection power at the SESOI, homogeneous / all-channel injection | 1.00 / 0.90 | 1.00 / 0.75 | 0.99 / ≈ 0.2 |
| Equivalence power at ±SESOI under the null | 1.00 | 1.00 | 1.00 |
| Equivalence power at ±0.03 (Q1 secondary) | 0.73 | 0.54 | — |
| False-positive rate (nominal 0.05) | 0.01–0.03 | 0.01 | 0.00–0.01 |

Both questions can bound a null at their SESOI. A homogeneous effect at the SESOI is detected. A rate-proportional effect is very unequal across experiments: at δ = 0.05 the injected Q1 ΔAUC ranges from 0.004 to 0.20 across dev units. That inflates between-experiment variance, so a heterogeneous Q2 growth of 0.02–0.03 would most likely be "inconclusive" rather than detected or bounded. Q1 can rule out effects of human size (0.059), not effects half that size.

## 8. Secondary families and sensitivity

- **Sensitivity (reported, not tested):**
  - 360-ms window with the same end (`--sensitivity L360`);
  - experiments ≥ DIV 15 (n = 8 Q1, 7 Q2);
  - all channels, unresidualized, and rank features (Q1).
- **Families S1–S5** as in spec 9, Benjamini–Hochberg q = 0.05 within family, labeled exploratory. Two S5 rows from paper v2 are defined here (D-066) and cannot change Q1/Q2:
  - **(a)** the (0,1)-vs-(0,0) decoder in the Q1 framework, with its own shift null;
  - **(b)** mirroring (our reading): the residualized pre-stimulus total-count contrast (0,1) − (1,0) vs the post-stimulus 25–300 ms contrast, Spearman ρ across experiments, shift-null p.

## 9. Code and environment

- **Frozen code:** `src/organoid_anticipation/`, `scripts/D_confirmatory.py`, `scripts/B1_build_experiments.py` at tag `prereg-v1`.
- **Environment lock:** `environment.lock.yml`, SHA-256 `c8364adf47b6bfa0de8980b30288f2a85e51909ecb2f1ac54f4c149c2483d3a2`. It matched the installed environment on 2026-10-28.
- **Seeds:** global seed 20261026; per-task seeds via `derive_seed(task)`.
- **Dev dry run** (permuted labels, full settings): `results/D/dev_permuted_primary/`.

Dry-run outcome (permuted labels, null by construction): Q1 estimate −0.005 (95% CI −0.030 to +0.021; 90% bound 0.025; randomization p 0.60) → A. Q2 estimate −0.005 (−0.013 to +0.004; randomization p 0.18) → A. No-growth-at-k ≥ 5 passes; swap-null means equal shift-null means (Q1 mean difference +0.001, Q2 −0.0003).

## Deviations (after freeze)

| Date | What changed | Why | Impact on interpretation |
|---|---|---|---|
