"""D: confirmatory run of Q1 and Q2 (spec v0.4; docs/preregistration.md). ONE run on the held-out split after the
preregistration is frozen (tag prereg-v1), both hard gates pass (results/B/B7/gates.json) and the PI confirms (CP4).

Usage
  python -I scripts/D_confirmatory.py --split dev --permuted     # dry run on dev with permuted labels
  python -I scripts/D_confirmatory.py --split heldout --i-have-cp2-signoff
      # the confirmatory run. Refuses unless: the tag prereg-v1 exists; every frozen file is identical to the tagged
      # version and uncommitted changes are absent; split.csv and environment.lock.yml match the registered hashes;
      # both hard gates passed. Commit, tag and file hashes are written into summary.json.
Steps
  1. Units (D-041): Q1 = session 1 of every unit in the split whose first session is 0; Q2 = units with 100 sessions
     in multi-experiment cultures. No unit is excluded for its response window (D-059).
  2. Build each unit (fixed 250-ms window ending at t0 - 15 ms; trials whose window overlaps a volley span dropped,
     D-060); label-free carryover ratio and descriptive decay per unit.
  3. Q1 per unit: residualized two-binary decoder on Q1 features (C = 1); sequence-shift null over every k in
     [16, 240] once; Delta-AUC_e = AUC - mean(null), v_e = var(null). Sensitivities: unresidualized, rank features,
     all channels; DIV >= 15 subset; window 360 ms (--sensitivity L360, separate run).
  4. Q2 per unit: G (10 blocks, C = 0.01), same shift null, Delta-G_e, v_e. Interpretation controls (D-065): per-block
     unresidualized AUC for s(n-1); growth for targets s(n+5), s(n+10) ("no growth at k >= 5", flagged); Q2 swap null.
  5. Pool per question (metafor rma.mv, culture/experiment, t, df = cultures - 1). Primary p-value: randomization test
     (one shift per experiment, REML refit, N_RAND draws). TOST at SESOI (Q1 0.059 fixed; secondary +-0.03; Q2 0.02);
     realized 90% CI as the achieved bound; BF10 (Cauchy, scale SESOI; 0.5x, 2x). Outcome A/B/C (spec 7, D-064).
  6. Sequence-swap null (8.5) for Q1 and Q2. Per-experiment injected sensitivity next to the forest plots (D-063).
  7. Exploratory family S5 (D-058/D-066): (a) (0,1)-vs-(0,0) contrast in the Q1 framework; (b) mirroring.
Outputs: results/D/<split>[_permuted]_<sensitivity>/{units.csv, q1_nulls.npz, forest_*.png/csv, summary.json}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from organoid_anticipation import derive_seed  # noqa: E402
from organoid_anticipation.models.pooling import bf10, pool, tost  # noqa: E402
from organoid_anticipation.pipeline import analysis as A  # noqa: E402
from organoid_anticipation.pipeline.experiment import build_experiment  # noqa: E402
from organoid_anticipation.synth.inject import channel_subset, inject_multiplicative  # noqa: E402

PREREG = dict(SESOI_Q1=0.059, SESOI_Q1_SECONDARY=0.03, SESOI_Q2=0.02, C_Q1=1.0, C_Q2=0.01, N_RAND=10000,
              N_SENS_Q1=20, SENS_DELTA_Q1=0.05, N_SENS_Q2=3, SENS_DELTA_Q2=0.1, ALPHA=0.05)
TAG = "prereg-v1"
FROZEN = ["src/organoid_anticipation", "scripts/D_confirmatory.py", "scripts/B1_build_experiments.py",
          "docs/preregistration.md", "docs/preregistration_values.json", "docs/analysis_spec.md", "environment.lock.yml"]
GATES = ROOT / "results/B/B7/gates.json"


def load_prereg():
    PREREG.update(json.loads((ROOT / "docs/preregistration_values.json").read_text()))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def git(*a) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def provenance(require_frozen: bool) -> dict:
    files = {}
    for p in FROZEN:
        q = ROOT / p
        for f in (sorted(q.rglob("*")) if q.is_dir() else [q]):
            if f.is_file() and "__pycache__" not in f.parts:
                files[str(f.relative_to(ROOT))] = sha256(f)
    split = ROOT / "data/manifests/split.csv"
    prov = dict(head_commit=git("rev-parse", "HEAD"), tag=TAG, tag_commit=git("rev-parse", "-q", "--verify", f"{TAG}^{{commit}}"),
                uncommitted_in_frozen=git("status", "--porcelain", "--untracked-files=all", "--", *FROZEN).splitlines(),
                changed_since_tag=git("diff", "--name-only", TAG, "--", *FROZEN).splitlines() if git("tag", "-l", TAG) else None,
                split_sha256=sha256(split), lock_sha256=sha256(ROOT / "environment.lock.yml"),
                gates_sha256=sha256(GATES) if GATES.exists() else None, file_sha256=files)
    if require_frozen:
        errs = []
        if not prov["tag_commit"]:
            errs.append(f"tag {TAG} does not exist")
        if prov["uncommitted_in_frozen"]:
            errs.append(f"uncommitted changes in frozen files: {prov['uncommitted_in_frozen']}")
        if prov["changed_since_tag"]:
            errs.append(f"frozen files differ from {TAG}: {prov['changed_since_tag']}")
        if prov["split_sha256"] != PREREG["SPLIT_SHA256"]:
            errs.append("split.csv hash differs from the registered value")
        if prov["lock_sha256"] != PREREG["LOCK_SHA256"]:
            errs.append("environment.lock.yml hash differs from the registered value")
        g = json.loads(GATES.read_text()) if GATES.exists() else {}
        if not (g.get("gate_a", {}).get("pass") and g.get("gate_b", {}).get("pass")):
            errs.append(f"hard gates not passed ({GATES})")
        if errs:
            sys.exit("held-out run refused:\n  " + "\n  ".join(errs))
    return prov


def unit_list(split):
    sys.path.insert(0, str(ROOT / "scripts"))
    from B1_build_experiments import units
    us = [u for u in units() if u["split"] == split]
    div = pd.read_csv(ROOT / "results/B/B1/div_check.csv").set_index("experiment_id").age_used_div
    for u in us:
        u["q1"] = u["first_session"] == 0
        u["q2"] = (len(u["sessions"]) == 100) and not u["single"]
        u["age_div"] = int(div[u["experiment_id"]])
    return us


def sequences(us, permuted):
    """Labels-only pre-pass: session-1 sequence (s) of every unit, for the sequence-swap nulls (8.5)."""
    from organoid_anticipation.io.d001611 import read_session
    out = {}
    for u in us:
        tr = read_session(ROOT / "data/raw/d001611" / u["paths"][0], load_spikes=False).trials
        s = tr[["s1", "s2"]].values[None].astype(np.uint8)
        o = np.array([list(map(int, b)) for b in tr.o_bits], np.uint8)[None]
        if permuted:
            s, o = A.permute_label_world(s, o, np.random.default_rng(derive_seed(f"D_perm_{u['unit']}")))
        out[u["unit"]] = s[0]
    return out


# ---------------------------------------------------------------- per-unit computations
def q1_block(e, s, o, incl, pool_, keep, rng):
    out, nulls = {}, {}
    variants = (("q1", True, "log1p", incl), ("q1_unresid", False, "log1p", incl),
                ("q1_rank", True, "rank", incl), ("q1_allch", True, "log1p", np.ones_like(incl)))
    for tag, resid, tf, inc in variants:
        P, Y = A.q1_prepare(e.W, e.R, s, o, inc, pool_, residualize=resid, transform=tf, keep=keep)
        out[f"{tag}_auc"] = A.score2(P, Y, PREREG["C_Q1"])
        nulls[tag] = np.array([A.score2(P, A.targets_for(P, A.shift_targets(s[:1], k)), PREREG["C_Q1"]) for k in A.SHIFTS])
        out[f"{tag}_null_mean"], out[f"{tag}_null_var"] = nulls[tag].mean(), nulls[tag].var(ddof=1)
    # injected sensitivity (label-free world: fresh random sequences; delta on all included channels, both sources)
    ch = channel_subset("all", incl, pool_, e.W, rng)
    inj = []
    for r in range(PREREG["N_SENS_Q1"]):
        s_r, o_r = A.permute_label_world(s, o, rng)
        Wi = inject_multiplicative(e.W, s_r, ch, PREREG["SENS_DELTA_Q1"], rng, [0], "both")
        Pi, Yi = A.q1_prepare(Wi, e.R, s_r, o_r, incl, pool_, keep=keep)
        inj.append(A.score2(Pi, Yi, PREREG["C_Q1"]) - out["q1_null_mean"])
    out["q1_sens_dAUC"] = float(np.mean(inj))
    return out, nulls


def contrast_rows(e, s, o, incl, pool_, keep):
    """Exploratory S5 (D-066). (a) (0,1)-vs-(0,0) decoder in the Q1 framework, session 1, with its own shift null
    (labels shifted, pair membership recomputed per shift). (b) mirroring inputs: residualized pre-stimulus and
    post-stimulus (25-300 ms) log1p total-count contrasts (0,1) minus (1,0), standardized; pre-contrast shift null."""
    y1 = (s[0, :, 0] + 2 * s[0, :, 1]).astype(int)
    X = A.q1_features(e.W[0], incl, pool_)
    H = A.history(s[:1], o[:1], e.R[:1], incl, pool_)[0]
    base = keep[0] if keep is not None else np.ones(A.T, bool)

    def pair_auc(yy):
        m = base.copy(); m[:2] = False
        m &= np.isin(yy, (0, 2))
        pos = np.flatnonzero(m)
        P = A.prepare(X[pos], H[pos], pos, np.zeros(len(pos), int))
        return A.score(P, (yy[pos] == 2).astype(int), PREREG["C_Q1"])

    def pre_contrast(yy):
        pos = np.flatnonzero(base & (np.arange(A.T) >= 2))
        P = A.prepare(X[pos][:, :1], H[pos], pos, np.zeros(len(pos), int))
        r = np.full(A.T, np.nan)
        for te, B in zip(P.te, P.Xte):
            r[pos[te]] = B[:, 0]                      # out-of-fold residualized, standardized log1p total
        a, b = r[(yy == 2)], r[(yy == 1)]
        a, b = a[np.isfinite(a)], b[np.isfinite(b)]
        return (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)

    out = dict(s5a_auc=pair_auc(y1))
    na = np.array([pair_auc(np.roll(y1, -k)) for k in A.SHIFTS])
    out.update(s5a_null_mean=na.mean(), s5a_null_var=na.var(ddof=1))
    post = np.log1p(e.R[0][:, incl].sum(1).astype(float))
    pos = np.flatnonzero(base & (np.arange(A.T) >= 2))
    a, b = post[pos][y1[pos] == 2], post[pos][y1[pos] == 1]
    out["s5b_post_contrast"] = (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    out["s5b_pre_contrast"] = pre_contrast(y1)
    nb = np.array([pre_contrast(np.roll(y1, -k)) for k in A.SHIFTS])
    return out, dict(s5a=na, s5b_pre=nb)


def q2_block(e, s, o, incl, pool_, keep, rng, seqs, unit):
    out, nulls = {}, {}
    H = A.history(s, o, e.R, incl, pool_, W=e.W, q2=True)
    Ps = [A.q2_prepare(e.W, e.R, s, o, incl, pool_, b, Hfull=H, keep=keep) for b in A.q2_blocks()]
    C = PREREG["C_Q2"]

    def G_of(target):
        a = np.array([A.score2(P, A.targets_for(P, target), C) for P in Ps])
        return A.q2_growth(a), a

    G, aucs = G_of(s)
    out.update({f"q2_auc_b{i+1}": v for i, v in enumerate(aucs)})
    out["q2_G"], out["q2_late_minus_b1"] = G, aucs[-1] - aucs[0]
    nulls["q2"] = np.array([G_of(A.shift_targets(s, k))[0] for k in A.SHIFTS])
    out["q2_null_mean"], out["q2_null_var"] = nulls["q2"].mean(), nulls["q2"].var(ddof=1)
    # interpretation controls (D-065)
    for k in (5, 10):
        out[f"q2_G_k{k}"] = G_of(A.shift_targets(s, k))[0]
    Pu = [A.q2_prepare(e.W, e.R, s, o, incl, pool_, b, residualize=False, keep=keep) for b in A.q2_blocks()]
    carry = np.array([A.score2(P, A.targets_for(P, A.shift_targets(s, -1)), C) for P in Pu])
    out.update({f"q2_carry_unresid_b{i+1}": v for i, v in enumerate(carry)})
    out["q2_carry_unresid_G"] = A.q2_growth(carry)
    sw = [G_of(np.broadcast_to(seq[None], s.shape))[0] for k, seq in seqs.items() if k != unit]
    out["q2_swap_mean"], out["q2_swap_sd"], out["q2_swap_n"] = float(np.mean(sw)), float(np.std(sw)), len(sw)
    # injected sensitivity: ramp to delta on all included channels, fresh random sequences
    ch = channel_subset("all", incl, pool_, e.W, rng)
    inj = []
    for r in range(PREREG["N_SENS_Q2"]):
        s_r, o_r = A.permute_label_world(s, o, rng)
        Wi = inject_multiplicative(e.W, s_r, ch, PREREG["SENS_DELTA_Q2"], rng, range(e.W.shape[0]), "both", ramp=True)
        Hr = A.history(s_r, o_r, e.R, incl, pool_, W=Wi, q2=True)
        Pr = [A.q2_prepare(Wi, e.R, s_r, o_r, incl, pool_, b, Hfull=Hr, keep=keep) for b in A.q2_blocks()]
        inj.append(A.q2_growth(np.array([A.score2(P, A.targets_for(P, s_r), C) for P in Pr])) - out["q2_null_mean"])
    out["q2_sens_dG"] = float(np.mean(inj))
    return out, nulls


def run_unit(u, permuted, sens, seqs):
    L_win = 0.360 if sens == "L360" else 0.250
    e = build_experiment([ROOT / "data/raw/d001611" / p for p in u["paths"]], u["sessions"], u["unit"], True, L_win=L_win)
    m = e.meta
    out = dict(unit=u["unit"], culture=u["culture_id"], age_div=u["age_div"], window_ms=m["window_len_s"] * 1e3,
               n_trials_dropped_overlap=m["n_windows_overlapping_volley_span"],
               carryover_ratio=m["carryover_ratio"], ref_over_pretask=m["ref_over_pretask"],
               rw_vs_within_task_two_sided_ms=";".join(f"{k}:{v*1e3:.0f}" for k, v in m["rw_vs_within_task_two_sided_s"].items()))
    s, o = e.s, e.o
    if permuted:
        s, o = A.permute_label_world(s, o, np.random.default_rng(derive_seed(f"D_perm_{u['unit']}")))
    rng = np.random.default_rng(derive_seed(f"D_unit_{u['unit']}"))
    incl = A.include_channels(e.W, e.w_len)
    pool_ = A.spatial_pools(e.xy, e.stim_xy)
    out["n_channels_incl"] = int(incl.sum())
    nulls = {}
    if u["q1"]:
        o1, n1 = q1_block(e, s, o, incl, pool_, e.w_ok, rng); out.update(o1); nulls.update(n1)
        P, _ = A.q1_prepare(e.W, e.R, s, o, incl, pool_, keep=e.w_ok)
        sw = [A.score2(P, seq[P.pos], PREREG["C_Q1"]) for k, seq in seqs.items() if k != u["unit"]]
        out["q1_swap_mean"], out["q1_swap_sd"], out["q1_swap_n"] = float(np.mean(sw)), float(np.std(sw)), len(sw)
        o5, n5 = contrast_rows(e, s, o, incl, pool_, e.w_ok); out.update(o5); nulls.update(n5)
    if u["q2"]:
        o2, n2 = q2_block(e, s, o, incl, pool_, e.w_ok, rng, seqs, u["unit"]); out.update(o2); nulls.update(n2)
    return out, nulls


# ---------------------------------------------------------------- pooling and decisions
def reml(d, yi, vi):
    return pool(pd.DataFrame(dict(rep=0, culture=d.culture, experiment=d.unit, yi=yi, vi=vi))).iloc[0]


def randomization(d, stat, nulls, null_mean_col, rng):
    """Primary p-value (spec 6.5, D-064): draw one shift-null value per experiment, refit the REML model, N_RAND times."""
    rows = []
    for r in range(PREREG["N_RAND"]):
        for u, c, mu, v in zip(d.unit, d.culture, d[null_mean_col], d.vi):
            rows.append((r, c, u, rng.choice(nulls[u][stat]) - mu, v))
    P = pool(pd.DataFrame(rows, columns=["rep", "culture", "experiment", "yi", "vi"]))
    P = P[P.converged]
    return P.est.values


def pooled_inference(df, stat, est_col, sesoi, nulls, rng, secondary=None, primary=True, subset=None):
    d = df[df[f"{stat}_null_var"].notna()].copy()
    if subset is not None:
        d = d[subset(d)]
    if d.empty:
        return {}
    d["yi"] = d[est_col] - d[f"{stat}_null_mean"]
    d["vi"] = d[f"{stat}_null_var"]
    p = reml(d, d.yi, d.vi)
    res = dict(n_units=len(d), n_cultures=int(d.culture.nunique()), est=p.est, se=p.se, df=p.df,
               ci95=[p.ci_lo, p.ci_hi], ci90=[p.ci90_lo, p.ci90_hi], p_reml=p.p,
               sigma2_culture=p.sigma2_culture, sigma2_exp=p.sigma2_exp,
               per_unit=d[["unit", "culture", "yi", "vi"]].to_dict("records"))
    if primary:
        draws = randomization(d, stat, nulls, f"{stat}_null_mean", rng)
        res["randomization_p"] = float((np.sum(np.abs(draws) >= abs(p.est)) + 1) / (len(draws) + 1))
        res["randomization_n_converged"] = int(len(draws))
    if sesoi:
        res["sesoi"] = sesoi
        res.update({f"tost_{k}": v for k, v in tost(p.est, p.se, p.df, sesoi).items()})
        res["achieved_bound_90ci"] = float(max(abs(p.ci90_lo), abs(p.ci90_hi)))
        res["estimate_vs_sesoi"] = float(p.est / sesoi)
        for f in (0.5, 1.0, 2.0):
            res[f"bf10_scale{f}"] = bf10(p.est, p.se, f * sesoi)
    if secondary:
        res.update({f"tost_secondary_{secondary}_{k}": v for k, v in tost(p.est, p.se, p.df, secondary).items()})
    if primary and sesoi:
        ci_excl0 = (p.ci_lo > 0) or (p.ci_hi < 0)
        rand_sig = res["randomization_p"] < PREREG["ALPHA"]
        if ci_excl0 and rand_sig:
            res["outcome"] = "B: candidate effect (95% CI excludes 0 and randomization p < 0.05); requires every Section 8 control to pass"
        elif res["tost_equivalent"]:
            res["outcome"] = f"A: bounded null (equivalence at +-{sesoi})"
        else:
            res["outcome"] = "C: inconclusive"
        res["ci_and_randomization_disagree"] = bool(ci_excl0 != rand_sig)
    return res


def forest(df, stat, est_col, sens_col, out, label):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = df[df[f"{stat}_null_var"].notna()].copy().sort_values(["culture", "unit"])
    d["delta"] = d[est_col] - d[f"{stat}_null_mean"]
    d["se"] = np.sqrt(d[f"{stat}_null_var"])
    d[["unit", "culture", "delta", "se", sens_col, "carryover_ratio"]].to_csv(out / f"forest_{stat}.csv", index=False)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 0.35 * len(d) + 1.5), sharey=True, gridspec_kw=dict(width_ratios=[3, 1]))
    y = np.arange(len(d))[::-1]
    a1.errorbar(d.delta, y, xerr=1.96 * d.se, fmt="o", color="k", ms=4, lw=1)
    a1.axvline(0, color="grey", lw=0.8)
    a1.set_yticks(y); a1.set_yticklabels(d.unit.str.replace("d001611_", ""), fontsize=7)
    a1.set_xlabel(f"{label} minus shift-null mean (95% interval of the shift null)")
    a2.barh(y, d[sens_col], color="#888")
    a2.set_xlabel("injected sensitivity")
    fig.tight_layout(); fig.savefig(out / f"forest_{stat}.png", dpi=130); plt.close(fig)


def mirroring(df, nulls, rng):
    d = df[df.s5b_pre_contrast.notna()]
    from scipy.stats import spearmanr
    obs = spearmanr(d.s5b_pre_contrast, d.s5b_post_contrast).statistic
    draws = np.array([spearmanr([rng.choice(nulls[u]["s5b_pre"]) for u in d.unit], d.s5b_post_contrast).statistic
                      for _ in range(PREREG["N_RAND"])])
    return dict(n_units=len(d), spearman_pre_vs_post=float(obs),
                sign_agreement=int((np.sign(d.s5b_pre_contrast) == np.sign(d.s5b_post_contrast)).sum()),
                p_shift=float((np.sum(np.abs(draws) >= abs(obs)) + 1) / (len(draws) + 1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["dev", "heldout"])
    ap.add_argument("--permuted", action="store_true")
    ap.add_argument("--sensitivity", default="primary", choices=["primary", "L360"])
    ap.add_argument("--n-jobs", type=int, default=12)
    ap.add_argument("--i-have-cp2-signoff", action="store_true")
    a = ap.parse_args()
    load_prereg()
    if a.split == "heldout" and (a.permuted or not a.i_have_cp2_signoff):
        sys.exit("held-out run requires --i-have-cp2-signoff and real labels")
    prov = provenance(require_frozen=(a.split == "heldout"))
    out = ROOT / "results/D" / f"{a.split}{'_permuted' if a.permuted else ''}_{a.sensitivity}"
    out.mkdir(parents=True, exist_ok=True)
    us = [u for u in unit_list(a.split) if u["q1"] or u["q2"]]
    seqs = sequences(us, a.permuted)
    res = Parallel(n_jobs=a.n_jobs)(delayed(run_unit)(u, a.permuted, a.sensitivity, seqs) for u in us)
    df = pd.DataFrame([r[0] for r in res])
    nulls = {r[0]["unit"]: r[1] for r in res}
    df.to_csv(out / "units.csv", index=False)
    np.savez_compressed(out / "nulls.npz", **{f"{u}__{k}": v for u, n in nulls.items() for k, v in n.items()})
    rng = np.random.default_rng(derive_seed(f"D_rand_{a.split}"))
    summ = dict(split=a.split, permuted=a.permuted, sensitivity=a.sensitivity, prereg=PREREG, provenance=prov,
                n_shifts=len(A.SHIFTS), shift_range=[int(A.SHIFTS.min()), int(A.SHIFTS.max())])
    q1 = dict(PRIMARY=pooled_inference(df, "q1", "q1_auc", PREREG["SESOI_Q1"], nulls, rng, secondary=PREREG["SESOI_Q1_SECONDARY"]))
    for tag in ("q1_unresid", "q1_rank", "q1_allch"):
        q1[tag] = pooled_inference(df, tag, f"{tag}_auc", PREREG["SESOI_Q1"], nulls, rng, primary=False)
    q1["div_ge_15"] = pooled_inference(df, "q1", "q1_auc", PREREG["SESOI_Q1"], nulls, rng, primary=False, subset=lambda d: d.age_div >= 15)
    q1["swap_minus_shift_null_mean"] = (df.q1_swap_mean - df.q1_null_mean).dropna().describe().to_dict()
    summ["Q1"] = q1
    if "q2_null_var" in df:
        q2 = dict(PRIMARY=pooled_inference(df, "q2", "q2_G", PREREG["SESOI_Q2"], nulls, rng))
        q2["div_ge_15"] = pooled_inference(df, "q2", "q2_G", PREREG["SESOI_Q2"], nulls, rng, primary=False, subset=lambda d: d.age_div >= 15)
        q2["late_minus_b1_secondary"] = pooled_inference(df, "q2", "q2_late_minus_b1", None, nulls, rng, primary=False)
        q2["late_minus_b1_secondary"]["note"] = "block 10 - block 1 against the G shift null (descriptive scale only)"
        ctrl = {}
        for k in (5, 10):
            r = pooled_inference(df, "q2", f"q2_G_k{k}", None, nulls, rng, primary=False)
            r["flag_investigate"] = bool(r["ci95"][0] > 0 or r["ci95"][1] < 0)
            ctrl[f"growth_k{k}"] = r
        ctrl["no_growth_at_k_ge_5_pass"] = not any(ctrl[f"growth_k{k}"]["flag_investigate"] for k in (5, 10))
        ctrl["carry_unresid_by_block_mean"] = df[[f"q2_carry_unresid_b{i}" for i in range(1, 11)]].mean().round(4).tolist()
        ctrl["carry_unresid_G"] = df.q2_carry_unresid_G.dropna().describe().to_dict()
        ctrl["swap_minus_shift_null_mean"] = (df.q2_swap_mean - df.q2_null_mean).dropna().describe().to_dict()
        q2["interpretation_controls"] = ctrl
        summ["Q2"] = q2
        forest(df, "q2", "q2_G", "q2_sens_dG", out, "Q2 growth G")
    forest(df, "q1", "q1_auc", "q1_sens_dAUC", out, "Q1 AUC")
    s5 = dict(a_01_vs_00=pooled_inference(df, "s5a", "s5a_auc", None, nulls, rng, primary=False),
              b_mirroring=mirroring(df, nulls, rng),
              note="Exploratory family S5 (D-066); BH within S5 at report time; cannot change Q1/Q2 decisions")
    summ["S5_exploratory"] = s5
    (out / "summary.json").write_text(json.dumps(summ, indent=1, default=float))
    print(json.dumps({k: summ[k] for k in ("Q1", "Q2") if k in summ}, indent=1, default=float)[:6000])


if __name__ == "__main__":
    main()
