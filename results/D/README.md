# results/D: confirmatory runs

- `dev_permuted_primary/`: **full dry run on the dev split, PERMUTED labels** (2026-10-28), `python -I scripts/D_confirmatory.py --split dev --permuted --n-jobs 6` at commit d5b81a9, with the final values in `docs/preregistration_values.json`. Labels are a per-unit position permutation (`derive_seed("D_perm_<unit>")`). Settings as registered: 225 shifts, 10,000 randomization draws, sensitivity and swap nulls. Results are null by construction:
  - **Q1** (14 units, 11 cultures): ΔAUC −0.005 (95% CI −0.030 to +0.021; 90% bound 0.025); randomization p 0.60; outcome A.
  - **Q2** (11 units, 8 cultures): ΔG −0.005 (−0.013 to +0.004); randomization p 0.18; outcome A.
  - No growth at k = 5, 10. Swap-null means equal shift-null means.

  Files: `units.csv`, `nulls.npz`, `forest_q1.png/csv`, `forest_q2.png/csv` (per-experiment injected sensitivity beside each forest plot), `summary.json` (with provenance hashes).
- An earlier dry run with provisional values is superseded by this one and is not included.
- On the held-out split (`--split heldout --i-have-cp2-signoff`) the script refuses unless the frozen files equal tag `prereg-v1`, the split and lock hashes match, and both gates passed (README.md, "The guard").
- `heldout_primary/`: **the single confirmatory run** (2026-10-28, 19:06–20:08), `python -I scripts/D_confirmatory.py --split heldout --i-have-cp2-signoff --n-jobs 12` at commit fe7a9d4, with frozen files identical to tag `prereg-v1` (71e5018; guard passed). Run after the gates passed and the design was signed off. Q1: ΔAUC +0.0034 (95% CI −0.026 to +0.033), randomization p 0.73 → A. Q2: ΔG +0.0036 (−0.006 to +0.013), p 0.29 → A. Q2 control s(n+5) flagged (VERIFICATION.md, section 4).
- `heldout_L360/`: pre-registered **sensitivity**, 360-ms window (20:08–21:13), same command with `--sensitivity L360`. Its outcome label is not used.
- Registered controls 8.2 (held-out), 8.3 and 8.11 (real dev labels) were run after the primary analysis (2026-10-28). Their outputs are not included here; their results are in the paper's Supplementary Information S5.
