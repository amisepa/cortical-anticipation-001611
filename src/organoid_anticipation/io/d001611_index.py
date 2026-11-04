"""Experiment/session index for DANDI 001611, built from the asset manifest only (no NWB reads).

Experiments are not labeled in DANDI. We derive them from the per-asset session description
("Detected spikes in session <k>"): within a subject, sorted by session start time, the session
counter restarts at 1 at each new experiment (verified: 27 runs of exactly 100 sessions).
IDs follow labeling_and_provenance Section 1.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def build_index(assets_tsv: Path) -> pd.DataFrame:
    a = pd.read_csv(assets_tsv, sep="\t", dtype={"subject": str})
    a["session_start"] = pd.to_datetime(a["session_start"], utc=True, format="ISO8601")
    a["orig_session_no"] = a["session_desc"].map(lambda s: int(re.search(r"session (\d+)", s).group(1)))
    a = a.sort_values(["subject", "session_start"]).reset_index(drop=True)
    # culture IDs ordered by subject ID string (stable, metadata-derived)
    cult = {s: f"d001611_C{i:02d}" for i, s in enumerate(sorted(a["subject"].unique()), start=1)}
    a["culture_id"] = a["subject"].map(cult)
    exp_no = []
    for _, g in a.groupby("subject", sort=False):
        e, last = 0, None
        for k in g["orig_session_no"]:
            if last is None or k <= last:
                e += 1
            exp_no.append(e)
            last = k
    a["exp_no"] = exp_no
    a["experiment_id"] = a["culture_id"] + "_E" + a["exp_no"].map("{:02d}".format)
    a["session_idx"] = a.groupby("experiment_id").cumcount()
    a["session_id"] = a["experiment_id"] + "_S" + a["session_idx"].map("{:03d}".format)
    return a[["culture_id", "experiment_id", "session_id", "subject", "orig_session_no", "session_start",
              "path", "size", "sha256", "asset_id"]]


def experiments(index: pd.DataFrame) -> pd.DataFrame:
    e = index.groupby(["culture_id", "experiment_id", "subject"]).agg(
        n_sessions=("session_id", "size"), start=("session_start", "min"), end=("session_start", "max"),
        size_bytes=("size", "sum"), sess_no_min=("orig_session_no", "min"), sess_no_max=("orig_session_no", "max"),
    ).reset_index()
    return e


def simultaneous_pairs(exps: pd.DataFrame, tol_s: float = 10.0) -> pd.DataFrame:
    """Experiments on different subjects whose first sessions start within tol_s seconds."""
    rows = []
    for i, a in exps.iterrows():
        for j, b in exps.iterrows():
            if j <= i or a.subject == b.subject:
                continue
            dt = abs((a.start - b.start).total_seconds())
            if dt <= tol_s:
                rows.append({"exp_a": a.experiment_id, "exp_b": b.experiment_id, "start_diff_s": round(dt, 3)})
    return pd.DataFrame(rows)
