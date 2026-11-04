# results/B/B7: hard gates before the held-out run (CP2 decision 2; spec 8.14; D-061)

Produced 2026-10-28 by `scripts/B7_gates.py all 6` at commit a163d6a, the commit that fixed the pass criteria before the gates were run. Inputs: dev builds `data/interim/d001611/exp/*.npz` from `scripts/B1_build_experiments.py` (fixed 250-ms window, D-059/D-060). For gate (b), the session-1 trials table of all 27 experiments (labels only). Seeds: `derive_seed("B7_gate_a_<q>_<unit>")`, `derive_seed("B7_gate_b_mc")`.

**Label use.** Gate (a) uses REAL dev labels with target s(n−1) only. No statistic relating W(n) to s(n) was computed. Gate (b) reads labels only, including held-out sequences (approved labels-only check).

| File | Content |
|---|---|
| `gates.json` | Pass/fail per gate, pooled numbers, commit |
| `gate_a_units.csv` | Per unit and question: real AUC for s(n−1) from residualized and unresidualized windows; permuted-world reference mean and variance; excess |
| `gate_a_pooled.csv` | REML-pooled excess per question, 95% CI, bound, pass |
| `gate_b_tests.csv` | 27 sequences × 16 Monte-Carlo tests: statistic, MC p, Holm p |
| `gate_b_global.csv` | Fisher combination per test over sequences, and cross-sequence position-dispersion tests; Bonferroni p |
