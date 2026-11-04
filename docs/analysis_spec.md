# Analysis Specification v0.4 (our spec, independent of the paper)

**v0.4 changes (28 Oct 2026, CP2 decisions; `docs/checkpoints/CP2_decisions_message.md`, review `docs/reviews/CP2_fable.md`; decisions D-053b, D-059…D-067):**
- **Window:** one fixed 250-ms window ending 15 ms before t₀ for every experiment, "stimulation-free, carryover residualized". No response-window exclusion or shortening; response windows are descriptive. Label-free carryover ratio reported per experiment. Sections 2, 3, 8.13.
- **Hard gates** before the held-out run: residualized W(n) cannot decode s(n−1); position-level randomness audit on all 27 sequences. Section 8.14.
- **Decision rules:** SESOI_Q1 = ΔAUC 0.059 fixed; realized 90% CI as the achieved bound; secondary TOST ±0.03; SESOI_Q2 = 0.02; randomization test is the primary p-value; outcome B decoupled from the SESOI. Section 7.
- **Shift null:** every k ∈ [16, 240] once. Section 6.5.
- **Q2:** C = 0.01 (plateau); interpretation controls (carryover trajectory, growth at k ≥ 5, swap null). Sections 6.1, 8.15.
- **Injection:** top-8 busiest channels replace 4 random channels; homogeneous and heterogeneous power side by side; per-experiment sensitivity next to the forest plots. Sections 8.1, 8.10.
- Exploratory S5 rows from paper v2 defined (Section 9). r(n−1) on no-observation trials aligned to the code (Section 5). Held-out counts (Section 10).

**v0.3 changes (27 Oct 2026, CP1 decisions; `docs/checkpoints/CP1.md`, review `docs/reviews/CP1_fable.md`):**

**v0.3 changes (27 Oct 2026, CP1 decisions; `docs/checkpoints/CP1.md`, review `docs/reviews/CP1_fable.md`):**
- Two pre-registered questions with separate decision rules: **Q1** (first exposure, the paper's question) and **Q2** (growth of pre-stimulus decodability across sessions: learned expectation and biological positive control). Sections 1, 1b, 7.
- Q1 features are low-dimensional (log1p total count plus three label-free spatial pools); Q2 uses per-channel counts. Section 4.
- Two binary decoders (s¹, s²). The 4-class multinomial option is removed. Section 6.
- **Inference at the position level throughout.** The sequence-shift null is the error source. No trial-level bootstraps and no per-trial χ² or Kruskal–Wallis tests. Section 6.
- Session-swap null replaced by a sequence-swap null. Section 8.
- CP1 parameter values filled in (Section 12): grid t₀, g = 15 ms, L_min = 250 ms, response window 710 ms (re-estimated per experiment and per y(n−1) category), blanking spans, channel rule 0.01 Hz.
- Pre-registered sensitivity analyses: RW = 610 ms; excluding experiments younger than DIV 15.
- Held-out split rules per question. Section 10.

**Status:** frozen at tag `prereg-v1` (CP2, 28 Oct 2026) once both CP2 hard gates (8.14) pass, together with `preregistration.md` and `preregistration_values.json`. Changes after that go in the preregistration's dated "Deviations" section and are labeled exploratory.

**Principle:** this is what we believe a correct test looks like. It was written from first principles and the literature, not copied from Cannard. Where our choices differ from the paper's, `paper_claims_audit.md` records how the paper's result would change.

---

## 1. Question and hypotheses

**Design constraint (A5, verified for the dev experiments read so far).** In 001611 and Isomura, each experiment presents one fixed 256-trial label sequence, repeated in every session. Within a sequence the draws look like independent fair coins. Across sessions they are not redrawn: from session 2 on, the upcoming label is a fixed function of trial position, and the culture has been exposed to it at that position before. Draws are unpredictable to the culture only on first exposure, in session 1.

The analysis therefore asks two questions, each with its own decision rule (Section 7).

**Q1 (primary; the paper's question: content anticipation of an unpredictable draw).** In session 1 of each experiment, does activity recorded *before* any stimulation on trial *n* contain information about the stimulus category of trial *n*, beyond what is explained by trial history?
- **H0₁:** pre-stimulus activity is conditionally independent of the upcoming category, given trial history.
- **H1₁:** it is not. Two-sided. Decoding performance is the test statistic.

**Q2 (secondary confirmatory; learned expectation and biological positive control).** Across the 100 sessions of an experiment, does pre-stimulus decodability of the upcoming category, after history residualization, **grow** relative to the start of training?
- **H0₂:** no change in history-residualized decodability across sessions.
- **H1₂:** decodability changes across sessions. Two-sided test; the expected direction under learning is positive.

Why Q2 is defined as growth rather than level: carryover from trial n−1 is present from session 1, and in a single fixed realization y(n−1) is correlated with y(n) by chance (A5: lag-1 χ² p as low as 0.011 across the 15 dev sequences). A *level* of decodability in later sessions therefore mixes carryover, chance sequence structure and learned expectation. Growth relative to session 1, after residualization, isolates what was learned.

**Not tested:**
- timing anticipation (impossible with fixed inter-trial intervals)
- anticipation in sessions ≥ 2 as a separate claim: Q2 addresses expectation there, and no anomalous interpretation is ever drawn from sessions ≥ 2

## 1b. What a positive result could mean (read before interpreting anything)

**Q1.** On first exposure the category is unpredictable to the culture. Conventional neuroscience predicts **zero** information about it before stimulation, once history is controlled. A non-null Q1 result can only come from:

1. leakage in the random-number generator or stimulation engine (draws correlated with something observable). Already found: the registration timestamps leak catch status by one sample (A5, D-033), which is why t₀ comes from the engine grid;
2. causation running from neural state to the draw (closed-loop designs);
3. analysis artifacts (leakage across CV folds, alignment bugs, selection effects from preprocessing);
4. **carryover combined with chance structure in the single realization:** the window lies 0.7–0.98 s after trial n−1's volley, so it carries y(n−1), and y(n−1) is correlated with y(n) by chance within that one sequence. History residualization (Section 5) and the sequence-shift null (8.4) are required for this reason;
5. chance;
6. a genuinely anomalous effect, which is what the paper tests and what the human "presentiment" literature claims.

The analysis must rule out 1–5 before 6 can be considered.

**Q2.** A positive Q2 result has an ordinary explanation: the culture has been exposed to the same sequence at the same positions many times, and sequence learning or position-specific expectation is plausible. Q2 is therefore the **biological positive control**: it shows whether the pipeline can see pre-stimulus label information in this preparation when a mechanism exists. It is never evidence of anomalous anticipation. Its alternative explanations are items 1–3 above and a growth in carryover strength (plasticity), which residualization addresses.

**How the two combine.** A Q1 null is most informative if Q2 is positive (the pipeline sees learned expectation but not first-exposure anticipation). A Q1 null with a Q2 null limits interpretation to "no detectable pre-stimulus label information of any kind at this sensitivity". The injection tests (8.1, 8.10) set the sensitivity of each question separately.

**No biological positive control exists for Q1's effect.** No known mechanism produces it, so Q1's sensitivity can only be shown by the injection test (8.1) and the closed-loop data (8.7), where pre-stimulus activity causes the stimulus.

Oddball and omission paradigms (Zhang 2025) test something different: prediction of *predictable* events, expressed after the stimulus.

**Report three things separately:**
- predictive processing (post-stimulus, learnable structure)
- expectation (sequence- or position-driven, pre-stimulus; Q2)
- anticipation of an unpredictable draw (Q1)

---

## 2. Definitions

| Term | Definition | Source of truth |
|---|---|---|
| Trial *n*, position | One draw of the hidden sources and the stimulation it triggers. **Position** = trial index 0–255 within the session; the same position carries the same label in every session of an experiment | NWB trial table |
| Sequence | The 256-trial (s, o) sequence of an experiment | NWB trial table; A5 |
| **t₀(n)** | Scheduled first pulse of trial n: a per-session Theil–Sen fit of the 1-s engine grid to the recorded trial times, plus the median detected volley onset offset (−5.2 ms in the dev experiment; re-estimated per experiment). Same rule for no-observation trials. The recorded start_time is never used directly (its jitter is label-dependent; D-033) | Engine grid (A3) |
| Volley | Label-free: ≥ 3 bins of 0.25 ms in which ≥ 10% of recording channels detect, within [start_time − 16 ms, start_time + 12 ms]; onset/offset = first/last such bin (D-029, D-051, D-052) | `events/volleys.py` |
| t_reg(n) | The dataset's "registration" timestamp. Used only to align with the paper's figures | NWB |
| **Targets** | **s¹(n)** and **s²(n)**, the two binary hidden sources, decoded separately. y₁ = s¹ + 2s² is used only for description. (0,0) is the no-observation trial (A4, D-003b) | Files plus author code |
| Secondary targets | **Y₂**: bit density of o(n) (varies only within classes (1,0), (0,1)). **Y₃** = [y₁ = 0] (no-observation), which is identical to "s¹ = s² = 0" | Files |
| Response window RW (descriptive only) | Time after the volley offset at which the smoothed evoked rate returns within ±10% of the **label-free within-task reference** (window rate on trials whose previous trial had no volley), per experiment and per evoking category (8.13). Also reported against the pre-task baseline. **Not used to exclude experiments or set the window** (D-059): at a 1-s trial interval the after-effects of trial n−1 outlast the inter-trial gap in most cultures | 8.13 |
| **Pre-stimulus window W(n): stimulation-free, carryover residualized** | [t₀(n) − g − L, t₀(n) − g], g = 15 ms, **L = 250 ms for every experiment** (D-059). Stimulation-free: no volley blanking span overlaps it (checked per trial; D-060). **Not carryover-free:** it lies ≈ 0.72–0.97 s after trial n−1's volley, inside its after-effects (label-free carryover ratio, window rate after a volley / after no volley, 0.15–1.99 across dev experiments). Carryover is handled by history residualization (Section 5) and the sequence-shift null (6.5), and checked by gate 8.14(a). The ratio is reported per experiment | B1 |
| Culture / experiment / session | Independent biological unit (DANDI subject) / a run of 100 sessions within a subject (author ID EXPnn) / a block of 256 trials | `labeling_and_provenance.md`; D-016, D-017 |

---

## 3. Inclusion and exclusion (applied blind to labels)

- **Sessions:** include unless a session has fewer than 256 trials, non-monotonic timestamps, missing volleys (volley-free count ≠ o-derived no-observation count), or total spike count below 1% of its experiment median. Log every exclusion with its reason.
- **Experiments:** an experiment whose session 1 is excluded is dropped from Q1. Q2 requires ≥ 90 included sessions. No experiment is excluded for its response window (D-059).
- **Trials:** include only if W(n) is stimulation-free (Section 2; a trial whose window overlaps any detected volley's blanking span is dropped, D-060). Drop the first 2 trials of each session (no history). Q1 therefore has up to 254 trials per experiment.
- **Channels:** recorded channels with ≥ 0.01 Hz artifact-free rate inside the clean windows over the whole experiment (label-free). Channels sitting on a stimulation electrode are excluded (none in the dev experiment; nearest is 17.5 µm). Sensitivity: all channels; ≥ 0.02 Hz.
- **Cultures:** include all that pass. Report the effective N per level.
- **Age (pre-registered sensitivity):** repeat Q1 and Q2 excluding experiments younger than DIV 15 at session 1 (young cultures may not yet support stable network responses; Zhang et al., *Eur. J. Neurosci.* 2026, as cited at CP1). Age comes from the files' DIV field, checked against recording dates per subject; where they disagree, age is derived from dates (D-036).
- **Stimulation-free windows exist for every trial** (verified on all 2,700 sessions; one trial dropped, D-060). The test is therefore possible as a **history-controlled** test. No window at a 1-s interval is free of trial n−1's after-effects; the comparison with the paper states that every "pre-stimulus" window in 001611 is the previous trial's after-effect. The lagged-response analysis (4c) runs only as a leakage diagnostic.

---

## 4. Features

**Counts are always transformed by log1p before standardization** (clean-window counts are heavy-tailed; max 458 in one dev window). Rank-transformed features are a sensitivity analysis.

**4a. Q1 features (four, label-free):**
- f₁ = log1p(total count over included channels in W(n));
- f₂–f₄ = log1p counts in three **spatial pools** defined from geometry only: pool A = included channels whose nearest stimulation electrode is one of o-bits 1–16 and lies within 100 µm; pool B = the same for o-bits 17–32; pool C = all other included channels.
- Pools A and B use the o-column ↔ stimulation-electrode mapping (column k ↔ k-th `stim_array` electrode), which is verified by the approved delivered-pattern check (labeling 4.2). If that check fails, A and B are replaced by "within 100 µm of any stimulation electrode" and C is split in two along the array's long axis.

**4b. Q2 features:** log1p per-channel counts in W(n), included channels only.

**4c. Lagged-response leakage diagnostic (all datasets, including Isomura):** decode s(n) from the evoked counts r(n−1), controlling for s(n−1) and o(n−1), with position-held-out CV. **This is not an anticipation test.** A non-null result points to random-number-generator, engine or analysis leakage, or to the chance sequence structure in item 4 of Section 1b. It is reported in the integrity results, never as evidence of anticipation.

**4d. Secondary features (exploratory):** per-channel counts for Q1 (expected to be underpowered; CP1 review); 100-ms bin profiles.

**Artifact handling:** remove detections on all channels from detected volley onset − 4 ms to offset + 3 ms. Moot for W(n), which ends ≥ 15 ms before the next onset; required for post-stimulus checks. Log counts removed.

---

## 5. History control (the key confound)

With 1-s inter-trial intervals and plasticity, pre-stimulus activity is shaped by recent trials, and in a single fixed realization recent history is correlated with y(n) by chance. History covariates **H(n)**:

**Q1 (254 trials; kept small):** s¹(n−1), s²(n−1), s¹(n−2), s²(n−2); the delivered bit counts of o(n−1) in bits 1–16 and 17–32; the log1p counts r(n−1) in 25–300 ms after t₀(n−1) (total and pools A, B, C; for no-observation trials these are the spontaneous counts in the same interval, D-067); trial index. 11 covariates.

**Q2 (adds):** session index; time since session start; per-session mean clean-window rate of the previous session (slow drift); r(n−1) per-channel principal components (k = 5, fitted on training folds); cumulative pulses delivered in the session. Category frequencies over the last 10 and 50 trials are included as well; with a fixed sequence they are position functions and are handled by the position-held-out folds.

**Never used:** recorded inter-trial intervals or start_time differences (label-dependent registration jitter; A5, D-033).

**Method: cross-fitted residualization.** Within each CV training fold only, regress each feature on H(n) (ridge, α = 1 on standardized H), then apply the fitted model to the test fold. Never fit residualization on data that includes test trials.

**Residualized decoding is primary for both questions.** Unresidualized decoding is reported alongside. In a single realization H(n) may be correlated with y(n) by chance, so residualization can remove a small part of a genuine signal; the sequence-shift null (8.4) is computed with the same residualization and accounts for this.

---

## 6. Primary statistic and model

1. **Decoder:** L2-regularized logistic regression on standardized, residualized features. Two binary decoders (s¹, s²). The experiment-level statistic is the mean of the two per-fold AUCs.
   - **Q1:** C = 1 (four standardized features, 254 trials; regularization strength is immaterial at this dimension; D-038).
   - **Q2:** **C = 0.01**, fixed from injection recovery on the dev split with permuted labels (D-053); injection recovery is flat from 10⁻⁴ to 10⁻² (D-053b).
2. **Cross-validation (position-aligned blocks).**
   - **Q1:** within session 1, 5 contiguous blocks of positions, with a 5-trial gap on each side of the test block removed from training.
   - **Q2:** sessions are grouped into 10 blocks of 10 consecutive sessions. Within each session block, fold b holds out the same position block [b·N/5, (b+1)·N/5) in every session of the block, with a 5-position gap on each side. Test positions never appear in training, so a position → label lookup cannot be learned.
3. **Score:** the mean of within-fold AUCs. Pooling out-of-fold scores across folds is biased below 0.5 with fixed sequences (A7, D-025).
4. **Q2 statistic:** AUC_b for each session block b = 1…10. The **growth** G_e = 9 × (OLS slope of AUC_b on b), i.e. the fitted change from block 1 (sessions 1–10, which contains session 1) to block 10 (sessions 91–100). Secondary contrast: AUC(sessions 91–100) − AUC(sessions 1–10), same block size. The pre-specified late block is **sessions 91–100**. Contrasting a late block against session 1 alone is not used as the primary statistic, because a decoder trained on one session has a tenth of the training data and its AUC is lower for that reason alone; a per-session descriptive curve with Q1 features (which anchors at session 1) is reported.
5. **Inference unit and error source (both questions).**
   - The unit of replication inside an experiment is the **trial position** (n = 254), not the trial: sessions repeat the same sequence. **No trial-level bootstraps and no per-trial χ² or Kruskal–Wallis tests** anywhere in this analysis; label-balance and engine-state tests are run on the 254 positions.
   - **Per-experiment null: sequence-shift.** Circularly shift the 256-label sequence by **every k ∈ [16, 240] exactly once** (225 shifts; D-062), the **same k in every session**; rerun the identical pipeline with the shifted sequence as the **target only**. H(n) is not shifted: it describes the physical history of the features (the real previous labels, delivered pattern and responses), so the residualized features are identical across shifts and only the target changes (D-048). The per-experiment effect is ΔAUC_e = AUC_e − mean(null_e) (Q1) or G_e − mean(null_e) (Q2), with sampling variance v_e = var(null_e).
   - **Pooling:** a three-level random-effects model with known sampling variances v_e: experiments nested in cultures (REML; `metafor::rma.mv`, random = ~1 | culture/experiment), with a t-distribution and df = number of cultures − 1 for the intercept. Report the grand mean, its 95% CI, τ_culture and τ_experiment.
   - **Primary p-value (D-064):** a randomization test of the pooled intercept that draws one shift-null value per experiment independently (10,000 draws) and refits the same REML model; p = share of draws with |estimate| at least as large as observed. The REML t-interval is used for estimation, the CI-based outcome rule and TOST.
   - **Descriptive:** per-experiment and per-culture forest plots.

---

## 7. Decision rule

**Effect sizes.** For a two-class contrast, ΔAUC = Φ(d/√2) − 0.5. The human presentiment pooled effect (≈ 0.21, treated as d) converts to **ΔAUC ≈ 0.059**. A floor of 0.01 (d ≈ 0.035) remains the conceptual smallest effect of interest, which these data cannot bound.

**Q1 (D-064).**
- **SESOI_Q1 = ΔAUC 0.059**, the human-effect equivalent, fixed whatever the number of held-out experiments.
- The realized **90% CI** of the pooled estimate is reported as the achieved bound.
- **Secondary (labeled):** TOST at ±0.03.
- Q1 can rule out effects of human size, not half that size (power: `results/B/B2/`).

**Q2.** **SESOI_Q2 = 0.02** (growth from block 1 to block 10, ΔAUC units).

**For each question:**
- **Equivalence:** TOST on the pooled estimate with bounds ±SESOI, α = 0.05 (90% REML CI inside the bounds).
- **Primary p-value:** the randomization test (6.5).
- **Bayes factor:** normal likelihood with the pooled estimate and SE, prior Cauchy(0, SESOI), two-sided. Robustness at 0.5× and 2× scale.
- **Outcomes:**
  - **(B) Candidate effect:** the 95% CI excludes 0 **and** the randomization p < 0.05, **and** every Section 8 control passes, whatever its size relative to SESOI. The size relative to SESOI is reported separately. For Q1, go to the plan's Section 9 gates. For Q2, report as learned expectation. *(Requiring both the CI and the primary p-value is our reading of the CP2 decision; disagreement between them is reported.)*
  - **(A) Bounded null:** not B, and equivalence shown. Report "no effect larger than ±SESOI".
  - **(C) Inconclusive:** neither. Report the CI and the achieved bound.
- Q1 and Q2 are separate families of one test each; no multiplicity correction between them. Sensitivity analyses (window 360 ms; DIV ≥ 15; all channels; unresidualized; rank features) are reported, not tested.

---

## 8. Controls (all required before interpreting either question)

| # | Control | Pass criterion |
|---|---|---|
| 8.1 | **Injection.** Add Poisson spikes so a channel's expected window count is multiplied by (1 + δ)^(s¹+s²) (or (1 + δ)^s¹), inside W(n), on real dev-split data with permuted labels. Channel subsets: all included channels, pools A+B, **top-8 busiest included channels** (replaces 4 random channels; D-063); ≥ 20 repeats. Reported side by side with **homogeneous** power (per-experiment effect D + N(0, v_e)) | Monotone recovery; false-positive rate at δ = 0 ≤ 0.05; reports MDE₈₀ per question (descriptive since D-064) |
| 8.2 | **Post-stimulus decoding.** Same pipeline on **25–300 ms** after t₀(n) (starts after the artifact tail) | AUC well above 0.5 in every experiment; otherwise labels or timestamps are misaligned |
| 8.3 | **Lag profile.** Decode s(n+k) from W(n) for k = −3…+10, position-held-out CV. For k ≤ −1 the history H must exclude the target's own lag (residualizing on the target biases AUC below 0.5: 0.44–0.45 on permuted dev labels; D-057); k ≤ −1 is reported unresidualized | A peak at k ≤ −1 (carryover) is expected. k ≥ 5 must be null; non-null means a sequence or engine artifact |
| 8.4 | **Sequence-shift null** (Section 6.5). Same k in every session | Gives the reported per-experiment null and the sampling variance |
| 8.5 | **Sequence-swap null.** Pair each experiment's features with the position-aligned labels of a *different* experiment's sequence (all other experiments in the same split; ~25 per experiment) | Null centered at the shift-null mean. Replaces the session-swap null, which is degenerate with repeated sequences |
| 8.6 | **Randomness audit.** Label autocorrelation, run lengths and balance; dependence on engine state; at the position level | No structure, or structure modeled explicitly |
| 8.7 | **Closed-loop positive control** (001132 activity-triggered trials, once their files are identified) | The pipeline *detects* "anticipation" there by construction |
| 8.8 | **Raw raster review.** Any effect is shown in spike rasters sorted by category | Human sees it at the checkpoint |
| 8.9 | **Preprocessing balance.** For every filtering step, compare the fraction removed across upcoming categories, **at the position level** (one row per position; permutation test over positions) | No category dependence |
| 8.10 | **Power at the realized design.** Rerun 8.1 with the actual trial and experiment counts. Q1: constant δ; designs "all dev units" and "9 cultures" (held-out-like). Q2: δ ramping linearly from 0 at session 1 to δ_max at session 100. **Per-experiment injected sensitivity** (Q1 δ = 0.05, Q2 ramp δ = 0.1, all channels) is computed in the confirmatory run and shown next to each forest plot | Describes power; SESOIs are fixed (D-064) |
| 8.11 | **Engine-timing leak.** Re-run the primary decoder with window anchors from the recorded start_time instead of the grid | Any difference flags timestamp leakage |
| 8.12 | **Position-lookup leak.** Naive by-session CV vs position-aligned CV on permuted fixed-sequence labels | Must show the A7 pattern (code sanity check) |
| 8.13 | **Evoked decay and carryover (descriptive).** Decay after volleys by y(n−1), per experiment, against the label-free within-task reference and the pre-task baseline; label-free carryover ratio per experiment | Reported; does not exclude or shorten anything (D-059) |
| 8.14 | **Hard gates before the held-out run (dev split; D-061).** (a) Residualized W(n) cannot decode s(n−1): real labels, target s(n−1) only; reference = the same statistic in permuted label worlds (H contains the target, so AUC is biased below 0.5; D-057); per-unit excess pooled with the primary REML model. (b) Position-level randomness audit on all 27 sequences: 16 Monte-Carlo tests per sequence vs iid fair coins, Holm over all; Fisher combination per test and two cross-sequence position-dispersion tests, Bonferroni; (0,0) ⇔ no delivered bits | (a) per question, 95% CI upper bound of the pooled excess < 0.03 (Q1) / 0.02 (Q2) and lower bound ≤ 0. (b) no rejection at 0.05 after correction; structural check exact. **Either fails: stop and report; no held-out run** |
| 8.15 | **Q2 interpretation controls (D-065).** (i) Per-block unresidualized AUC for s(n−1) and its growth (carryover trajectory); (ii) growth G for targets s(n+5) and s(n+10) against the same shift null, pooled; (iii) Q2 sequence-swap null | (ii) "no growth at k ≥ 5": **flagged** if either pooled 95% CI excludes 0; a flag means investigate, not automatically an artifact. (i), (iii) reported |

---

## 9. Secondary analyses (labeled; Benjamini–Hochberg FDR at q = 0.05 within each family)

- **Family S1 (replication of the paper):** per-session OLS-HC1 with the paper's regressors; DerSimonian–Laird random effects; Stouffer; 10/12 coherence. Then the same with HAC standard errors and experiment nesting. (The paper's "elapsed ITI" regressor is reproduced as written and flagged as label-leaking.)
- **Family S2 (paper's other tests):** per-electrode, ramping, bit-density, mirroring. Our definitions are logged in `decisions_log.md`.
- **Family S3 (secondary targets):** Y₂, Y₃ through the Q1 pipeline.
- **Family S4 (cross-dataset):**
  - Isomura (leakage diagnostic only; 4c)
  - Potter probe order
  - 001336 periodic stimulation (human organoids)
  - DishBrain is not public (OSF HTTP 401); dropped unless the data request succeeds
- **Family S5 (order and expectation):** non-linear run-length models (Schwarzkopf 2014); per-session Q2 curve; and two rows from paper v2, defined before the freeze (D-066): **(a)** the (0,1)-vs-(0,0) contrast in the Q1 framework (session 1, those two categories, residualized Q1 features, own shift null, primary pooling); **(b)** mirroring, our reading: per experiment, the residualized pre-stimulus total-count contrast (0,1) − (1,0) vs the post-stimulus (25–300 ms) contrast (0,1) − (1,0), Spearman ρ across experiments, shift-null p. Neither can change the Q1/Q2 decisions.

Spontaneous-activity comparisons across species, preparation, age and hardware follow **Section 13**.

---

## 10. Data split and blinding

- **Held-out split (saved before any outcome analysis; D-026):** grouped by experiment. In each multi-experiment culture, ⌈50%⌉ of experiments are held out. In the four single-experiment cultures (C02, C06, C10, C12), sessions 000–049 and 050–099 were assigned to dev/held-out at random.
- **Q1 confirmatory set:** session 1 of every held-out experiment; for single-experiment cultures, only if the held-out half contains session 1 (C02 only). **13 experiments in 9 cultures.** Five are younger than DIV 15 at session 1 (C01_E02, C04_E01, C05_E02, C07_E01, C09_E01), so the age sensitivity has 8 experiments in 6 cultures (D-067).
- **Q2 confirmatory set:** held-out experiments of multi-experiment cultures, **12 experiments in 8 cultures** (age sensitivity: 7 in 5). **The single-experiment cultures are excluded** from the Q2 confirmatory test (both halves carry the same sequence and culture; the split is not independent). They are reported descriptively.
- **Sequence-reuse check (labels only, approved at CP1):** compare held-out sequences with each other and with dev sequences, including circular shifts and source swaps. Any reuse is reported; an experiment whose sequence matches a dev sequence is flagged and analysed both with and without it.
- **Blinding:** dev work uses permuted labels until CP2, except the real-label post-stimulus checks approved at CP1 (labeling 4.2, off-by-one, 8.2, 8.13, Isomura 4c). After CP2, real labels on the dev split only. The held-out split runs once, after the spec is frozen and tagged.

---

## 11. Reporting

- Effective N at each level (cultures, experiments, sessions, positions, trials, channels), per question.
- Per question: pooled ΔAUC (Q1) or growth G (Q2) with 95% CI, TOST result and BF.
- Forest plots per experiment and per culture.
- Results of every control.
- All deviations from this spec.

---

## 12. Parameters (decided at CP1, 27 Oct 2026)

| Parameter | Candidates | Decided | Rationale / evidence |
|---|---|---|---|
| Targets | 4-class / two binaries | **Two binary decoders (s¹, s²)**; multinomial removed | Power (127 vs 127 per binary; CP1 review); code is binary (D-037) |
| t₀ for catch trials | engine schedule / matched latency | **Engine grid for all trials** | Grid residuals ±0.025 ms; start_time jitter is label-dependent (D-002b, D-033) |
| Response window | 300 ms / empirical | **Descriptive only (CP2, D-059).** Not used for exclusion or window length. Sensitivity window **360 ms** (formerly "RW = 610 ms") with the same end | CP2 review issue 1 |
| Guard g | 10 ms / other | **15 ms** | Grid-t₀ vs onset SD 0.45 ms, range ±3.5 ms |
| Window length L | 100 / 250 / 500 ms | **250 ms for every experiment** (Section 2; D-059) | Stimulation-free for every trial. 500 ms is rejected because it keeps only trials after a no-observation trial, i.e. it conditions on y(n−1) = 0, a deterministic position selection in a fixed sequence (position-level balance p = 0.30; D-030b) |
| Artifact blanking | ±1 ms / other | **Volley onset − 4 ms to offset + 3 ms, all channels** | D-007b |
| Channel inclusion | 0.1 Hz / other | **≥ 0.01 Hz in clean windows (label-free)** | 544/955 channels in the dev experiment |
| Count transform | raw / log1p / rank | **log1p**; ranks as sensitivity | Heavy tails |
| Q1 features | per-channel / low-dim | **Total + 3 spatial pools** | Per-channel decoder has no power at n = 254 (CP1 review) |
| SESOI | ≥ 0.01 | **Q1: 0.059 fixed (secondary ±0.03). Q2: 0.02** | Section 7; D-064 |
| Inference | trial bootstrap / position-level | **Sequence-shift null (k = 16…240, once each); three-level REML pooling; randomization test as primary p** | Section 6.5; D-062, D-064 |
| Age sensitivity | — | **Exclude experiments < DIV 15** | D-036 |
| Age-matching rule (13.3) | stage bin / functional anchor | **Stage bins primary**; functional anchor as sensitivity for longitudinal sets | CP1 |
| Burst detection (13.4) | relative threshold | **Provisional** (CP1 table); tuned in Phase E on 2 dev recordings per dataset, then frozen | CP1 |

---

## 13. Cross-species and cross-preparation comparison (spontaneous activity)

**Status:** exploratory. Estimation and description only; no confirmatory claims. Runs in Phase E. Starts after CP1, whatever the 001611 outcome.

### 13.1 Aims

- **A. Test the paper's calibration claims** (audit C11–C13: stimulation-free organoids are "arrhythmic", ~0.02 spikes/s, and "never" show a 1-s cadence) across species and preparations on matched hardware.
- **B. Profile intrinsic dynamics** (rates, bursts, rhythms, synchrony, sequences) per species and preparation. These background dynamics are what could masquerade as pre-stimulus structure, and they guide which preparation to use if the project reaches the bench.
- **C. Be explicit about what can't be compared yet.** The anticipation test itself can't be compared across species with public data:
  - human organoid stimulation exists only as 001336 (fixed interval, 3 subjects);
  - **no mouse organoid stimulation data is public.**

  Species comparisons in this section are therefore about **spontaneous dynamics**, not anticipation.

### 13.2 Coverage matrix (verify every cell at A1; fill in n per cell in `results/E/species_matrix.md`)

| Preparation | Human | Mouse | Rat |
|---|---|---|---|
| Whole organoid | 001603 HO (sorted only) | 001603 MO; 001374 (dorsal/ventral forebrain, days 23–64) | — |
| Organoid slice | Sharf 2022 (MaxWell + Neuropixels); Zenodo 14544729 | — | — |
| Tissue slice | 001132 (adult hippocampus, surgical) | 001603 MS (neonatal); MEA-seqX (3Brain) | — |
| 2D dissociated | Kapucu (hPSC, Axion); KCL (dissociated organoids, Axion); Zenodo 14544729; DishBrain (not public) | DishBrain (not public) | 001603 Pr; 002020; Kapucu; 001611; Potter; Isomura |
| **Stimulation data** | 001336 (organoid); 001132 (slice); DishBrain not public | none (DishBrain not public) | 001611; Isomura; Potter |

### 13.3 Matching rules (a contrast is interpretable only if these hold; otherwise label it with the confound)

1. **Primary species contrast:** human vs mouse organoids **within 001603 only**: same hardware family, same spike-sorting pipeline. Secondary contrast: human vs rat 2D **within Kapucu** (same Axion setup).
2. **Protocol:** record it for every group (guided cortical vs unguided cerebral; named protocol). If protocols differ, as is likely for human vs mouse in 001603, label the contrast **"species × protocol"**, not "species".
3. **Age:** compare by developmental stage, not calendar days; mouse tissue matures much faster than human. Tag both `age_days` (days since induction or DIV) and `dev_stage`. `dev_stage` is either a stage bin defined per protocol from the source papers, or a **functional anchor**: days since the first recording showing network bursts. Report the main contrast at matched stage and a sensitivity analysis at matched calendar age.
4. **Data level:** compare at the same level. If one group is sorted-units-only, use sorted units for both. Multiunit threshold crossings are used only when raw data exists for both groups.
5. **Hardware:** cross-platform contrasts use only recording-normalized metrics (13.4, "robust" column) and are labeled **hardware-confounded**. Never compare raw rates across platforms.
6. **Recording length:** truncate to a common duration (the shortest recording, at least 3 minutes), or report duration-matched estimates with confidence intervals.
7. **Unit of analysis:** the organoid, slice or culture. Repeated recordings of the same unit get a random effect.

### 13.4 Metrics (one code path; every recording)

| Metric | Raw form | Robust form (cross-hardware) |
|---|---|---|
| Firing rate | Median and distribution per unit or channel; fraction active | Rank-normalized within recording; fraction active |
| Network bursts | Rate, duration, inter-burst interval CV | Same (detected relative to each recording's own baseline) |
| Rhythmicity | Population-rate spectrum peaks | Peak frequency; peak-to-surrogate ratio |
| **1-s recurrence** | The paper's 1-s band recurrence (our reading, logged); autocorrelation at 1.0 ± 0.1 s | Compared against ISI-preserving shuffled surrogates (95th percentile) |
| Synchrony | STTC distribution (10 ms) | Same |
| Sequences (optional) | Fraction of backbone units (van der Molen definitions) | Same |

### 13.5 Statistics

- Mixed model per metric: `metric ~ group + dev_stage + (1 | unit) [+ (1 | dataset)]`. Report estimates with 95% CIs; Benjamini–Hochberg FDR across metrics.
- **Claim C13 test:** the proportion of recordings per group whose 1-s recurrence exceeds the surrogate 95th percentile. Any reproducible rhythmic recording at ~1 Hz in a stimulation-free organoid falsifies "never". Also report rhythms at other frequencies (e.g. the 2–3 Hz events reported in mature organoids, Trujillo 2019).

### 13.6 Outputs

- `results/E/species_matrix.md`: coverage with verified n per cell, protocol, age range and data level.
- Forest plots per metric by group (raw and robust).
- Updated `paper_claims_audit.md` rows C11–C13.
- A **preparation profile table** (rates, burstiness, rhythmicity, data availability) to inform any later wet-lab choice.

### 13.7 Gaps and requests

- **Mouse organoid stimulation:** Robbins et al. (mouse cortical organoids, MaxOne, closed-loop and random-electrode training) did not deposit data; request drafted in `docs/data_requests/robbins.md`.
- **Organoid stimulation with random timing (any species):** none public. This is the main justification for future wet-lab work.
