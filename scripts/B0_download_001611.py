"""B0: bulk download of DANDI 001611 (approved at CP1, decision 5). Spikes-only NWB, 2,700 files, ~39.9 GB.

Files go to data/raw/d001611/<asset path>. Each file is sha256-verified against the DANDI asset checksum.
Already-present files with a matching size are only re-hashed. Nothing downloaded is executed.
Writes data/manifests/provenance/d001611_bulk.csv (one row per asset). The combined data/manifests/provenance.csv
and results/A/A2/provenance.csv are rebuilt from data/manifests/provenance/*.csv afterwards (B1 session, 2026-10-27).
Usage: python -I scripts/B0_download_001611.py [n_workers]
"""
import datetime as dt
import hashlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/d001611"
VERSION = "0.260611.0634"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(r) -> dict:
    dest = RAW / r.path
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://api.dandiarchive.org/api/assets/{r.asset_id}/download/"
    status = None
    for attempt in range(3):
        if not (dest.exists() and dest.stat().st_size == int(r.size)):
            tmp = dest.with_suffix(dest.suffix + ".part")
            p = subprocess.run(["curl", "-sS", "-L", "--fail", "--retry", "5", "--retry-delay", "5", "-o", str(tmp), url])
            if p.returncode != 0:
                tmp.unlink(missing_ok=True)
                status = f"DOWNLOAD_FAIL rc={p.returncode}"
                continue
            tmp.rename(dest)
        got = sha256(dest)
        if got == r.sha256:
            status = "VERIFIED"
            break
        status = f"CHECKSUM_MISMATCH got={got}"
        dest.unlink()
    return dict(source="d001611", asset_path=r.path, version=VERSION, url=url, size=r.size, sha256=r.sha256,
                repo_checksum=f"sha256:{r.sha256}", status=status,
                access_date=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                local_path=str(dest.relative_to(ROOT)))


def main(n_workers: int = 8):
    idx = pd.read_csv(ROOT / "data/manifests/d001611_index.csv", dtype=str)
    # dev split first (Phase B needs it), then held-out (label-free integrity and labels-only checks)
    split = pd.read_csv(ROOT / "data/manifests/split.csv")
    idx["sess"] = idx.session_id.str[-3:].astype(int)
    dev = set()
    for r in split[split.split == "dev"].itertuples():
        g = idx[idx.experiment_id == r.experiment_id]
        if r.unit != "experiment":
            lo, hi = map(int, r.unit.split("_")[1].split("-"))
            g = g[(g.sess >= lo) & (g.sess <= hi)]
        dev |= set(g.session_id)
    idx["dev"] = idx.session_id.isin(dev)
    idx = idx.sort_values(["dev", "experiment_id", "sess"], ascending=[False, True, True])
    rows = []
    with ThreadPoolExecutor(n_workers) as ex:
        futs = [ex.submit(fetch, r) for r in idx.itertuples()]
        for i, f in enumerate(as_completed(futs), 1):
            rows.append(f.result())
            if i % 100 == 0:
                print(i, "done;", sum(x["status"] != "VERIFIED" for x in rows), "not verified", flush=True)
    out = pd.DataFrame(rows).sort_values("asset_path")
    pdir = ROOT / "data/manifests/provenance"
    pdir.mkdir(exist_ok=True)
    out.to_csv(pdir / "d001611_bulk.csv", index=False)
    print(out.status.value_counts().to_string())


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8)
