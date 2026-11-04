"""Organoid anticipation project: readers, timeline, audits, decoding and nulls."""
import hashlib

GLOBAL_SEED = 20261026


def derive_seed(task: str) -> int:
    """Deterministic per-task seed from the global seed (CLAUDE.md conventions). Log the returned value."""
    h = hashlib.sha256(f"{GLOBAL_SEED}:{task}".encode()).digest()
    return int.from_bytes(h[:4], "little")
