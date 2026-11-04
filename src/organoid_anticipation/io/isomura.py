"""Reader for Isomura et al. 2023 `invitro/response_data_<cond>.mat` (third_party/isomura, read-only).

Each file holds `data_<cond>`: an (n_cultures, 1) cell of structs with fields
  s (25600 x 2)  hidden sources, o (25600 x 32) stimulation bits, r (25600 x 64) evoked counts per electrode.
25600 = 100 sessions x 256 trials (verified A2). Rows are in trial order.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy.io as sio

N_TRIALS = 256


@dataclass
class Culture:
    cond: str
    idx: int          # 0-based position in the .mat cell array
    culture_id: str   # isomura_<cond>_C<nn>
    s: np.ndarray     # (n_sess, 256, 2) uint8
    o: np.ndarray     # (n_sess, 256, 32) uint8
    r: np.ndarray     # (n_sess, 256, 64) float

    @property
    def n_sessions(self):
        return self.s.shape[0]


def load_condition(path: str | Path) -> list[Culture]:
    path = Path(path)
    cond = path.stem.replace("response_data_", "")
    cell = sio.loadmat(path)[f"data_{cond}"]
    out = []
    for i in range(cell.shape[0]):
        c = cell[i, 0]
        s, o, r = (np.asarray(c[k][0, 0]) for k in ("s", "o", "r"))
        n = s.shape[0]
        assert n % N_TRIALS == 0 and o.shape[0] == n and r.shape[0] == n
        k = n // N_TRIALS
        out.append(Culture(cond, i, f"isomura_{cond}_C{i + 1:02d}", s.reshape(k, N_TRIALS, 2),
                           o.reshape(k, N_TRIALS, 32), r.reshape(k, N_TRIALS, -1).astype(float)))
    return out
