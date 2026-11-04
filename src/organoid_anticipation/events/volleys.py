"""Label-free reconstruction of stimulation volleys from spike detections (001611 has no stim-event table).

A stimulation pulse on a CMOS MEA produces a near-simultaneous artifact detection on most recording
channels. We bin all detections at `bin_ms` and call a bin "mass" when at least `frac` of recording
channels detect in it. Per trial we look in [t_start - pre, t_start + post] for mass bins.
Nothing here reads trial labels (s, o).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def mass_bins(spike_t: np.ndarray, n_channels: int, bin_s: float = 0.25e-3, frac: float = 0.10):
    """Return centers (s) and counts of bins with >= frac * n_channels detections."""
    b = np.floor(spike_t / bin_s).astype(np.int64)
    u, c = np.unique(b, return_counts=True)
    m = c >= frac * n_channels
    return (u[m] + 0.5) * bin_s, c[m]


def trial_volleys(t_start: np.ndarray, spike_t: np.ndarray, n_channels: int, pre: float = 0.016,
                  post: float = 0.012, bin_s: float = 0.25e-3, frac: float = 0.10, min_bins: int = 3) -> pd.DataFrame:
    """Per trial: has_volley, onset/offset of mass bins relative to t_start (s), number of mass bins,
    detections in the window. Also returns mass bins not attributable to any trial window.
    A volley needs >= min_bins mass bins (real volleys: >= 6 bins in the dev split; a single synchronous bin
    from a spontaneous network burst inside the window is not a volley; B3, D-051). pre = 16 ms: in C11_E03 volleys
    start at about -9 ms and as early as -12.6 ms re start_time, beyond the original 12-ms window (D-052)."""
    centers, counts = mass_bins(spike_t, n_channels, bin_s, frac)
    st = np.sort(spike_t)
    rows = []
    used = np.zeros(len(centers), bool)
    for k, t in enumerate(t_start):
        lo, hi = np.searchsorted(centers, [t - pre, t + post])
        used[lo:hi] = True
        n_det = np.searchsorted(st, t + post) - np.searchsorted(st, t - pre)
        if hi - lo >= min_bins:
            rows.append((k, True, centers[lo] - t, centers[hi - 1] - t, hi - lo, n_det))
        else:
            rows.append((k, False, np.nan, np.nan, 0, n_det))
    df = pd.DataFrame(rows, columns=["trial_idx", "has_volley", "on_rel_s", "off_rel_s", "n_mass_bins", "n_det_window"])
    extra = pd.DataFrame({"t": centers[~used], "count": counts[~used]})
    return df, extra
