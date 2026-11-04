"""B1: build per-experiment timeline, response window, clean windows and features for 001611.

Dev split: full build (labels stored for permuted-label development and the approved post-stimulus checks).
Held-out split: label-free timeline summary only (grid, volleys, pooled response window, window length);
no feature arrays and no labels are written (blinding, CLAUDE.md).
Single-experiment cultures: only the sessions of the dev half are built (dev) / summarized (held-out half).
Requires every session file of the unit to be present and sha256-verified (data/manifests/provenance/d001611_bulk.csv
or the A2 provenance).
Usage: python -I scripts/B1_build_experiments.py [dev|heldout|all] [n_jobs]
Outputs: data/interim/d001611/exp/<unit>.npz/.json/_decay.csv (dev); results/B/B1/units.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from organoid_anticipation.pipeline.experiment import build_experiment, save  # noqa: E402

OUT = ROOT / "data/interim/d001611/exp"
RES = ROOT / "results/B/B1"


def _sha256(f: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with f.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def units():
    idx = pd.read_csv(ROOT / "data/manifests/d001611_index.csv", dtype=str)
    idx["sess"] = idx.session_id.str[-3:].astype(int)
    split = pd.read_csv(ROOT / "data/manifests/split.csv")
    ver = set()
    for f in (ROOT / "data/manifests/provenance").glob("d001611*.csv"):
        p = pd.read_csv(f, dtype=str)
        ver |= set(p[p.status == "VERIFIED"].asset_path)
    p = pd.read_csv(ROOT / "data/manifests/provenance.csv", dtype=str)
    ver |= set(p[(p.source == "d001611") & (p.status == "VERIFIED")].asset_path)
    out = []
    for r in split.itertuples():
        g = idx[idx.experiment_id == r.experiment_id].sort_values("sess")
        name = r.experiment_id
        if r.unit != "experiment":
            lo, hi = map(int, r.unit.split("_")[1].split("-"))
            g = g[(g.sess >= lo) & (g.sess <= hi)]
            name = f"{r.experiment_id}_S{lo:03d}-{hi:03d}"
        complete = True
        for path, size, sha in zip(g.path, g["size"], g.sha256):
            if path in ver:
                continue
            f = ROOT / "data/raw/d001611" / path
            if not (f.exists() and f.stat().st_size == int(size) and _sha256(f) == sha):
                complete = False
                break
            ver.add(path)
        out.append(dict(unit=name, experiment_id=r.experiment_id, culture_id=r.culture_id, split=r.split,
                        single=bool(r.single_experiment_culture), first_session=int(g.sess.min()),
                        paths=list(g.path), sessions=list(g.session_id), complete=complete))
    return out


def run(u):
    dev = u["split"] == "dev"
    try:
        e = build_experiment([ROOT / "data/raw/d001611" / p for p in u["paths"]], u["sessions"], u["unit"], use_labels=dev)
    except Exception as ex:  # noqa: BLE001
        return dict(unit=u["unit"], status=f"ERROR {type(ex).__name__}: {ex}")
    if dev:
        save(e, OUT / f"{u['unit']}.npz")
    m = e.meta
    fmt = lambda d: ";".join(f"{k}:{v*1e3:.0f}" for k, v in d.items())  # noqa: E731
    return dict(unit=u["unit"], status="OK", window_rule=m["window_rule"], n_sessions=m["n_sessions"], n_channels=m["n_channels"],
                onset_offset_ms=m["onset_offset_s"] * 1e3, window_ms=m["window_len_s"] * 1e3, base_rate_hz=m["base_rate_hz"],
                min_gap_after_prev_volley_span_ms=m["min_gap_window_start_after_prev_volley_span_s"] * 1e3,
                n_windows_overlapping_volley_span=m["n_windows_overlapping_volley_span"],
                rw_vs_pretask_ms=fmt(m["rw_vs_pretask_baseline_s"]),
                within_task_ref_hz=m.get("within_task_ref_hz"), ref_over_pretask=m.get("ref_over_pretask"),
                carryover_ratio=m.get("carryover_ratio"),
                rw_vs_within_task_two_sided_ms=fmt(m["rw_vs_within_task_two_sided_s"]) if "rw_vs_within_task_two_sided_s" in m else None,
                rw_vs_within_task_elevation_ms=fmt(m["rw_vs_within_task_elevation_s"]) if "rw_vs_within_task_elevation_s" in m else None,
                period_min=min(m["period_s"]), period_max=max(m["period_s"]),
                n_unattributed_mass_bins=m["n_unattributed_mass_bins"],
                mean_clean_count_per_trial=float(e.W[:, 2:].sum(-1).mean()),
                subject_description=m["subject_description"])


def main(which="dev", n_jobs=8):
    RES.mkdir(parents=True, exist_ok=True)
    us = [u for u in units() if which == "all" or u["split"] == which]
    todo = [u for u in us if u["complete"]]
    print(f"{len(todo)}/{len(us)} units complete on disk", flush=True)
    rows = Parallel(n_jobs=n_jobs)(delayed(run)(u) for u in todo)
    df = pd.DataFrame(rows).merge(pd.DataFrame(us).drop(columns=["paths", "sessions"]), on="unit", how="right")
    f = RES / "units.csv"
    if f.exists():
        old = pd.read_csv(f)
        old = old[old.columns.intersection(df.columns)]      # drop columns of the superseded RW rule (D-059)
        df = pd.concat([old[~old.unit.isin(df.unit[df.status.notna()])], df[df.status.notna()]]).drop_duplicates("unit", keep="last")
    df.sort_values("unit").to_csv(f, index=False)
    print(df[["unit", "split", "status", "window_ms", "carryover_ratio", "ref_over_pretask"]].to_string())


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "dev", int(sys.argv[2]) if len(sys.argv) > 2 else 8)
