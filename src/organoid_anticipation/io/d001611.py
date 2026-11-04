"""Reader for DANDI 001611 session files -> common schema (labeling_and_provenance Section 3).

File facts (verified in A2 on the dev subset; see results/A/schema_report.md):
- One NWB file per session. `intervals/trials` has start_time, stop_time, s (256x2), o (256x32).
- `units` holds one threshold-detection "unit" per recording channel (channel_id), spike_times.
- Times are stored in **milliseconds** although NWB requires seconds. We detect this from the
  1000-unit trial spacing and convert to seconds; `time_unit_in_file` records what was found.
- There is no stimulation-event table. The o bits are the only record of what was delivered.
- Electrodes: group `rec_array` (recording channels) and `stim_array` (32 stimulation electrodes).
The reader uses h5py directly (read-only) so it doesn't depend on the NWB unit attributes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import h5py
import numpy as np
import pandas as pd


@dataclass
class Session:
    meta: dict
    trials: pd.DataFrame
    spikes: pd.DataFrame
    channels: pd.DataFrame
    stim_electrodes: pd.DataFrame
    warnings: list = field(default_factory=list)


def _s(x):
    return x.decode() if isinstance(x, bytes) else str(x)


def infer_time_scale(trial_starts: np.ndarray) -> tuple[float, str]:
    """Return (factor to seconds, unit label). 001611 trials are 1 s apart (preprint); spacing ~1000 => ms."""
    step = float(np.median(np.diff(trial_starts)))
    if 900 <= step <= 1100:
        return 1e-3, "ms"
    if 0.9 <= step <= 1.1:
        return 1.0, "s"
    raise ValueError(f"unexpected trial spacing {step}")


def read_session(path: str | Path, key: dict | None = None, load_spikes: bool = True) -> Session:
    key = key or {}
    warn = []
    with h5py.File(path, "r") as f:
        tr = f["intervals/trials"]
        st_raw = tr["start_time"][:]
        scale, unit = infer_time_scale(st_raw)
        if unit != "s":
            warn.append(f"times stored in {unit}; converted to s")
        s = tr["s"][:].astype(int)
        o = tr["o"][:].astype(int)
        trials = pd.DataFrame({
            "trial_idx": np.arange(len(st_raw)),
            "t_start": st_raw * scale,
            "t_stop": tr["stop_time"][:] * scale,
            "s1": s[:, 0], "s2": s[:, 1],
            "y1": s[:, 0] + 2 * s[:, 1],  # 0=(0,0) 1=(1,0) 2=(0,1) 3=(1,1); see decisions_log A4
            "o_bits": ["".join(map(str, r)) for r in o],
            "n_bits_on": o.sum(1),
        })
        trials["is_catch"] = trials.n_bits_on == 0
        e = f["general/extracellular_ephys/electrodes"]
        gname = e["group_name"][:].astype(str)
        el = pd.DataFrame({"electrode_id": e["id"][:], "x_um": e["x"][:], "y_um": e["y"][:], "group": gname})
        stim = el[el.group == "stim_array"].reset_index(drop=True)
        stim["stim_bit"] = np.arange(len(stim))  # assumed: o column k <-> k-th stim_array row (A4 note)
        rec = el[el.group == "rec_array"].reset_index(drop=True)
        u = f["units"]
        ch = u["channel_id"][:]
        idx = u["spike_times_index"][:]
        counts = np.diff(np.r_[0, idx])
        if load_spikes:
            t = u["spike_times"][:] * scale
            spikes = pd.DataFrame({"t": t, "channel_id": np.repeat(ch, counts)})
        else:
            spikes = pd.DataFrame(columns=["t", "channel_id"])
        d = np.sqrt((rec.x_um.values[:, None] - stim.x_um.values[None]) ** 2 + (rec.y_um.values[:, None] - stim.y_um.values[None]) ** 2)
        channels = pd.DataFrame({"channel_id": ch, "n_spikes": counts}).merge(
            rec.rename(columns={"electrode_id": "channel_id"}), on="channel_id", how="left")
        dmin = pd.Series(d.min(1), index=rec.electrode_id.values)
        channels["dist_to_stim_um"] = channels.channel_id.map(dmin)
        channels["is_stim_electrode"] = channels.dist_to_stim_um < 1.0
        if load_spikes:
            spikes = spikes.merge(channels[["channel_id", "x_um", "y_um"]], on="channel_id", how="left")
        sub = f["general/subject"]
        meta = {
            **key,
            "orig_path": str(path),
            "identifier": _s(f["identifier"][()]),
            "session_description": _s(f["session_description"][()]),
            "session_start_time": _s(f["session_start_time"][()]),
            "subject_id": _s(sub["subject_id"][()]),
            "species": _s(sub["species"][()]),
            "strain": _s(sub["strain"][()]) if "strain" in sub else None,
            "subject_description": _s(sub["description"][()]) if "description" in sub else None,
            "age": _s(sub["age"][()]) if "age" in sub else None,
            "device_attrs": {k: _s(v) for k, v in f["general/devices/HD-MEA"].attrs.items()},
            "filtering": sorted(set(e["filtering"][:].astype(str))) if "filtering" in e else None,
            "time_unit_in_file": unit,
            "n_trials": len(trials),
            "n_rec_channels": len(rec), "n_stim_electrodes": len(stim), "n_units": len(ch),
        }
    return Session(meta, trials, spikes, channels, stim, warn)
