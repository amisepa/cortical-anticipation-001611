"""A2 (part 1): 001611 experiment index and the held-out split (spec Section 10).

Label-blind: uses only the DANDI asset manifest (subject, session start, session counter).
Writes:
  data/manifests/d001611_index.csv     one row per session with derived IDs
  data/manifests/split.csv             experiment -> dev/heldout (cultures with 1 experiment: contiguous session halves)
  results/A/A2/experiments.csv, results/A/A2/simultaneous_pairs.csv
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from organoid_anticipation import derive_seed  # noqa: E402
from organoid_anticipation.io.d001611_index import build_index, experiments, simultaneous_pairs  # noqa: E402

SEED_TASK = "split_d001611"


def main():
    idx = build_index(ROOT / "data/manifests/d001611.assets.tsv")
    exps = experiments(idx)
    assert (exps.n_sessions == 100).all() and len(exps) == 27, exps
    out = ROOT / "results/A/A2"
    out.mkdir(parents=True, exist_ok=True)
    exps.to_csv(out / "experiments.csv", index=False)
    simultaneous_pairs(exps).to_csv(out / "simultaneous_pairs.csv", index=False)

    seed = derive_seed(SEED_TASK)
    rng = np.random.default_rng(seed)
    rows = []
    for cult, g in exps.groupby("culture_id"):
        ids = sorted(g.experiment_id)
        if len(ids) == 1:
            # spec 10: split sessions by contiguous halves; which half is held out is random
            first_held = bool(rng.integers(2))
            for half in (0, 1):
                rows.append({"culture_id": cult, "experiment_id": ids[0], "unit": f"sessions_{'000-049' if half == 0 else '050-099'}",
                             "split": "heldout" if (half == 0) == first_held else "dev", "single_experiment_culture": True})
            continue
        n_held = math.ceil(len(ids) / 2)
        held = set(rng.choice(ids, size=n_held, replace=False))
        for e in ids:
            rows.append({"culture_id": cult, "experiment_id": e, "unit": "experiment",
                         "split": "heldout" if e in held else "dev", "single_experiment_culture": False})
    split = pd.DataFrame(rows)
    split["seed_task"], split["seed"] = SEED_TASK, seed
    split.to_csv(ROOT / "data/manifests/split.csv", index=False)
    split.to_csv(out / "split.csv", index=False)
    idx.to_csv(ROOT / "data/manifests/d001611_index.csv", index=False)
    print(split.groupby(["single_experiment_culture", "split"]).size())
    print("seed", seed)


if __name__ == "__main__":
    main()
