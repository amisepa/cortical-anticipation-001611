"""Compare this snapshot's files with the SHA-256 values recorded by the confirmatory run.
Usage: python check_hashes.py   (from the folder holding this file)"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rec = json.loads((ROOT / "results/D/heldout_primary/summary.json").read_text())["provenance"]
print(f"run at commit {rec['head_commit'][:7]}, frozen at tag {rec['tag']} ({rec['tag_commit'][:7]})")
bad = 0
for rel, sha in rec["file_sha256"].items():
    p = ROOT / rel
    if not p.exists():
        print(f"MISSING  {rel}"); bad += 1; continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    status = "match" if h == sha else "DIFFERS"
    bad += status != "match"
    print(f"{status:8s} {rel}")
for name, key in (("data/manifests/split.csv", "split_sha256"), ("results/B/B7/gates.json", "gates_sha256")):
    h = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    print(f"{'match' if h == rec[key] else 'DIFFERS':8s} {name}")
print("expected: every file matches")
print("all frozen files match" if bad == 0 else f"{bad} file(s) differ or are missing")
