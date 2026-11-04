# results/B/B2: power at the realized design (spec 8.1, 8.10), PERMUTED labels, dev split

Re-run 2026-10-28 after the CP2 decisions by `scripts/B2_power.py all 10` at commit a163d6a. Inputs: the fixed-window dev builds `data/interim/d001611/exp/*.npz` (D-059). Seeds: `derive_seed("B2_world_<unit>_rep<k>")` (label worlds), `derive_seed("B2_q1_<unit>")`, `derive_seed("B2_q2_<unit>_0.01")`, `derive_seed("B2_q1_design")`, `derive_seed("B2_q2_design")`, `derive_seed("B2_homog_<q>")`. Real labels are never related to W(n). The CP2 run (`git show 597adec:results/B/B2/`) is superseded.

**Design.**
- **Q1:** 14 dev units with session 1 (11 cultures). Designs: "full" (all 14) and "ho9" (9 of 11 cultures at random each repetition, all their units; mimics the held-out 13 experiments in 9 cultures, df = 8). 100 repetitions.
- **Q2:** 11 dev units with 100 sessions in multi-experiment cultures (8 cultures); 20 repetitions.
- **Nulls:** every shift in [16, 240] once.
- **Injection subsets:** all included channels, pools A+B, top-8 busiest channels (D-063).
- **Homogeneous:** per-unit estimate D + N(0, v_e), 300 repetitions.
- **Power** = P(95% REML CI excludes 0).

## Headline

| | Q1 full (14 units) | Q1 ho9 (9 cultures) | Q2 (11 units) |
|---|---|---|---|
| 80% detection, homogeneous effect | ΔAUC 0.031 | 0.036 | ΔG 0.013 |
| 80% detection, injection on all channels (heterogeneous) | 0.054 | 0.063 | 0.050 |
| 80% detection, injection on pools A+B / top-8 | 0.049 / 0.074 | 0.060 / 0.088 | 0.080 / 0.090 |
| Detection power at the SESOI (homogeneous / all-channel injection) | 1.00 / 0.90 (at 0.06) | 1.00 / 0.75 (at 0.06) | 0.99 / ≈ 0.2 (at 0.02) |
| Equivalence power under the null at ±SESOI (injection nulls / homogeneous) | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| Equivalence power at ±0.03 (Q1 secondary) | 0.73 / 0.72 | 0.54 / 0.56 | — |
| False-positive rate at nominal 5% (injection nulls / homogeneous) | 0.03 / 0.013 | 0.01 / 0.007 | 0.00 / 0.013 |
| Mean pooled SE under the null | 0.0105 | 0.0117 | 0.0041 |

**Reading.** Under a true null, both questions bound effects at their SESOI. A homogeneous effect at the SESOI is detected. A rate-proportional injection makes per-experiment effects very unequal: at δ = 0.05, the injected Q1 ΔAUC ranges from 0.004 to 0.20 across units (`q1_unit_sensitivity.csv`). That inflates τ² and the SE, so detection needs larger pooled effects. A real heterogeneous Q2 growth of 0.02–0.03 would most likely come out "inconclusive", not "bounded null".

## Files

| File | Content |
|---|---|
| `q1_nulls.csv`, `q1_null_summary.csv` | Per-unit 225-shift null of the Q1 statistic (SD 0.034–0.038) |
| `q1_injection_auc.csv`, `q1_pooled_reps.csv`, `q1_power.csv`, `q1_mde80.csv`, `q1_tost_power_null.csv` | Injection (heterogeneous) power, both designs |
| `q1_homog_*`, `q2_homog_*` | Homogeneous power |
| `q1_power_side_by_side.csv`, `q2_power_side_by_side.csv` | Power by pooled effect: homogeneous vs each injection scenario (interpolated on the mean pooled estimate) |
| `q1_unit_sensitivity.csv`, `q2_unit_sensitivity.csv` | Per-unit injected effect at δ = 0.05 (Q1) / ramp δ = 0.1 (Q2) |
| `q2_nulls.csv`, `q2_null_summary.csv`, `q2_injection_G.csv`, `q2_pooled_reps.csv`, `q2_power.csv`, `q2_mde80.csv`, `q2_tost_power_null.csv` | Q2 (SD of the G null 0.010–0.013) |
| `q2_choose_C.csv` | CP2 choice of C (D-053; plateau D-053b) |
