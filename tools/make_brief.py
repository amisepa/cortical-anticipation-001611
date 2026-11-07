"""Build brief/: four plain-language figures (PNG + CSV each) and a two-page PDF.

Saved outputs only. Nothing here reads recordings or recomputes any held-out statistic.
Inputs
  results/D/heldout_primary/summary.json, forest_q1.csv, forest_q2.csv   (held-out run, 2026-10-28)
  results/B/B2/q1_power.csv, q1_homog_power.csv, q2_power.csv, q2_homog_power.csv  (injection power, dev split, permuted labels)
  PROVENANCE.md and Supplementary Information S6 of the paper (timeline; the run start/end are re-read from run.log here)
Also writes results.json (every number the brief cites, each with its source file; one copy in brief/, one at the top
level) and pdf_text.txt.
Usage: python tools/make_brief.py [--preview DIR] [--check TEXT.md]
  --preview DIR   also writes each PDF page as PNG into DIR, for checking
  --check FILE    after building, checks every number in FILE and in the PDF text against results.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "brief"
OUT.mkdir(parents=True, exist_ok=True)
HP = ROOT / "results/D/heldout_primary"
B2 = ROOT / "results/B/B2"

ANNOT = []  # every annotation string drawn on the figures (checked against results.json by --check)


def note(txt):
    ANNOT.append(txt); return txt


# Palette: one blue, neutral inks.
BLUE, BLUE_LIGHT, ORANGE = "#2a78d6", "#cde2fb", "#eb6834"
INK, INK2, MUTED, GRID, AXIS = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({"font.size": 9.5, "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.titlecolor": INK, "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": "DejaVu Sans"})

# ----------------------------------------------------------------------------------------------------------------------
# Saved numbers
S = json.loads((HP / "summary.json").read_text())
Q1, Q2 = S["Q1"]["PRIMARY"], S["Q2"]["PRIMARY"]
SESOI_Q1, SESOI_Q1_SEC, SESOI_Q2 = S["prereg"]["SESOI_Q1"], S["prereg"]["SESOI_Q1_SECONDARY"], S["prereg"]["SESOI_Q2"]
assert (SESOI_Q1, SESOI_Q1_SEC, SESOI_Q2) == (0.059, 0.03, 0.02)

# Cross-check against the values reported in the paper (rounded as printed there).
assert round(Q1["est"], 3) == 0.003 and [round(x, 3) for x in Q1["ci95"]] == [-0.026, 0.033] and round(Q1["randomization_p"], 2) == 0.73
assert round(Q2["est"], 3) == 0.004 and [round(x, 3) for x in Q2["ci95"]] == [-0.006, 0.013] and round(Q2["randomization_p"], 2) == 0.29
assert Q1["outcome"].startswith("A") and Q2["outcome"].startswith("A")
assert Q1["tost_equivalent"] and Q1["tost_secondary_0.03_equivalent"] and Q2["tost_equivalent"]

# ----------------------------------------------------------------------------------------------------------------------
# (a) Timeline. Times from PROVENANCE.md and Supplementary Information S6; tag time and run start/end re-read here.
def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()

tag_iso = git("for-each-ref", "--format=%(taggerdate:iso-strict)", "refs/tags/prereg-v1")
if tag_iso:  # inside the analysis repository: re-check the tag time against the figure
    assert tag_iso.startswith("2026-10-28T16:19:20"), tag_iso
else:  # this repository does not carry the original tag: the tag time is taken from PROVENANCE.md, section 1
    print("note: no git tag prereg-v1 here; tag time 16:19:20 PDT taken from PROVENANCE.md, section 1")
log = (HP / "run.log").read_text().splitlines()
assert log[0].startswith("Wed Oct 28 19:06:44 PDT 2026") and log[-1].startswith("Wed Oct 28 20:08:13 PDT 2026"), (log[0], log[-1])

D = dt.date(2026, 10, 28)
def T(h, m, s=0):
    return dt.datetime(D.year, D.month, D.day, h, m, s)

EVENTS = [  # (time, label, where, source)
    (T(16, 19, 20), "Analysis frozen\n(git tag prereg-v1)", "our machine", "git for-each-ref refs/tags/prereg-v1"),
    (T(19, 6, 44), "Held-out run\nstarted", "our machine", "results/D/heldout_primary/run.log, first line"),
    (T(19, 15, 8), "Code and tag\npushed to GitHub", "third party", "Supplementary Information S6 (.git reflog, update by push)"),
    (T(19, 51, 0), "Registered\non OSF (nxsph)", "third party", "Supplementary Information S6 (OSF display time, PDT)"),
    (T(19, 58, 46), "First per-experiment\noutput written", "our machine", "Supplementary Information S6 (file birth time of units.csv)"),
    (T(20, 8, 13), "Run finished,\nsummary written", "our machine", "results/D/heldout_primary/run.log, last line"),
    (T(21, 13, 29), "First result\ndisplayed", "our machine", "Supplementary Information S6 (session log; summary.json access time 21:13:34)"),
]
pd.DataFrame([dict(time_pdt=t.strftime("%Y-%m-%d %H:%M:%S"), event=l.replace("\n", " "), where=w, source=s)
              for t, l, w, s in EVENTS]).to_csv(OUT / "a_timeline.csv", index=False, lineterminator="\n")


def draw_timeline(fig, spec):
    ax = fig.add_subplot(spec)
    t0, t1 = T(16, 0), T(21, 30)
    hours = lambda t: (t - T(0, 0)).total_seconds() / 3600  # noqa: E731
    ax.set_xlim(hours(t0) - 0.08, hours(t1)); ax.set_ylim(-2.3, 2.9)
    ax.axvspan(hours(T(19, 6, 44)), hours(T(20, 8, 13)), color=BLUE_LIGHT, alpha=0.6, lw=0, zorder=0)
    ax.axvspan(hours(T(20, 8, 13)), hours(T(21, 13, 29)), color=GRID, alpha=0.55, lw=0, zorder=0)
    ax.text(hours(T(19, 8)), 2.85, "held-out run (no output seen)", ha="left", va="top", color=INK2, fontsize=7.8)
    ax.text(hours(T(20, 10)), 2.45, "sensitivity run (results unread)", ha="left", va="top", color=INK2, fontsize=7.8)
    ax.axhline(0, color=AXIS, lw=1.2, zorder=1)
    levels = [1.0, -1.0, 1.9, -1.9, 1.0, -1.0, 1.0]  # stem height; sign = above/below
    align = ["center", "center", "center", "right", "center", "left", "center"]  # 19:51 leans left, 20:08 leans right
    for (t, lab, where, _), lv, ha in zip(EVENTS, levels, align):
        x = hours(t); up = 1 if lv > 0 else -1
        mk, col = ("D", ORANGE) if where == "third party" else ("o", BLUE)
        ax.plot([x, x], [0, lv * 0.55], color=AXIS, lw=1, zorder=2)
        ax.plot(x, 0, mk, color=col, ms=8 if mk == "o" else 7, mec="white", mew=1.2, zorder=3)
        dx = {"center": 0, "left": 0.03, "right": -0.03}[ha]
        ax.text(x + dx, lv * 0.55 + 0.07 * up, f"{t:%H:%M}\n{lab}", ha=ha, va="bottom" if up > 0 else "top", fontsize=8.3, color=INK, linespacing=1.25)
    ax.set_yticks([]); ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)
    xt = list(range(16, 22))
    ax.set_xticks(xt); ax.set_xticklabels([f"{h}:00" for h in xt]); ax.tick_params(axis="x", length=0, pad=2)
    ax.set_xlabel("28 October 2026, Pacific time", labelpad=4)
    ax.set_title("(a) When things happened", loc="left", fontweight="bold", pad=6)
    h1 = plt.Line2D([], [], marker="o", color=BLUE, ls="", mec="white", ms=8, label="timestamp on our machine")
    h2 = plt.Line2D([], [], marker="D", color=ORANGE, ls="", mec="white", ms=7, label="third-party timestamp (GitHub, OSF)")
    ax.legend(handles=[h1, h2], loc="lower left", frameon=False, fontsize=8.3, bbox_to_anchor=(0.0, 0.0))
    return ax


# ----------------------------------------------------------------------------------------------------------------------
# (b), (c) Forest plots from the saved per-experiment CSVs and the saved pooled estimate.
def short(u):  # d001611_C02_E01_S000-049 -> C02 E01 (sessions 0-49)
    p = u.replace("d001611_", "").split("_")
    s = f"{p[0]} {p[1]}"
    if len(p) > 2:
        lo, hi = p[2][1:].split("-"); s += f" (sessions {int(lo)}-{int(hi)})"
    return s


def forest_table(csv, q):
    d = pd.read_csv(csv)
    d["experiment"] = d.unit.map(short)
    d["ci_low"] = d.delta - 1.96 * d.se; d["ci_high"] = d.delta + 1.96 * d.se
    keep = ["experiment", "unit", "culture", "delta", "se", "ci_low", "ci_high"]
    out = d[keep].copy()
    out.loc[len(out)] = ["Pooled (all experiments)", "pooled", "", q["est"], q["se"], q["ci95"][0], q["ci95"][1]]
    return d, out


D1, T1 = forest_table(HP / "forest_q1.csv", Q1)
D2, T2 = forest_table(HP / "forest_q2.csv", Q2)
assert len(D1) == Q1["n_units"] == 13 and len(D2) == Q2["n_units"] == 12
# The pooled estimate is a REML multilevel fit (saved); check it sits near the inverse-variance mean of the rows.
for d, q in ((D1, Q1), (D2, Q2)):
    w = 1 / d.se**2; assert abs((w * d.delta).sum() / w.sum() - q["est"]) < 0.01
T1.to_csv(OUT / "b_q1_forest.csv", index=False, lineterminator="\n"); T2.to_csv(OUT / "c_q2_forest.csv", index=False, lineterminator="\n")


def draw_forest(fig, spec, d, q, title, band, lines, xlabel, unit_name):
    ax = fig.add_subplot(spec)
    n = len(d); y = np.arange(n)[::-1] + 1
    ax.axvspan(-band, band, color=BLUE_LIGHT, alpha=0.55, lw=0, zorder=0)
    ax.text(band, n + 0.9, note(f"±{band:g}: effects this small or smaller\ncount as 'not meaningful' (set before the run)"),
            ha="right", va="bottom", fontsize=8, color=INK2)
    for l_ in lines:
        ax.axvline(l_, color=MUTED, lw=1, ls=(0, (3, 2)), zorder=1)
        ax.axvline(-l_, color=MUTED, lw=1, ls=(0, (3, 2)), zorder=1)
    if lines:
        ax.text(lines[-1], -0.78, note(f"±{lines[-1]:g}: stricter bound (secondary)"), ha="center", va="center", fontsize=7.6, color=MUTED)
    ax.axvline(0, color=AXIS, lw=1, zorder=1)
    ax.hlines(y, d.delta - 1.96 * d.se, d.delta + 1.96 * d.se, color=INK2, lw=1.4, zorder=2)
    ax.plot(d.delta, y, "o", color=BLUE, ms=6, mec="white", mew=0.9, zorder=3)
    lo, hi = q["ci95"]; e = q["est"]
    ax.fill([lo, e, hi, e], [0, 0.32, 0, -0.32], color=BLUE, lw=0, zorder=3)
    ax.set_yticks(list(y) + [0]); ax.set_yticklabels(list(d.experiment) + ["Pooled (all experiments)"], fontsize=8.5)
    ax.get_yticklabels()[-1].set_fontweight("bold")
    ax.set_ylim(-1.15, n + 1.6)
    xmax = max(abs(d.delta - 1.96 * d.se).max(), abs(d.delta + 1.96 * d.se).max(), band) * 1.12
    ax.set_xlim(-xmax, xmax)
    ax.set_xlabel(xlabel); ax.grid(axis="x", color=GRID, lw=0.7); ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_title(title, loc="left", fontweight="bold", pad=20)
    ax.text(xmax, 0.0, note(f"pooled {e:+.3f}\n95% CI {lo:+.3f} to {hi:+.3f}"), ha="right", va="center", fontsize=8.3, color=INK)
    return ax


# ----------------------------------------------------------------------------------------------------------------------
# (d) Detection rate vs injected effect (dev split, permuted labels; results/B/B2). x = mean realized pooled effect.
def power_curve(csv, design, sub, scenario):
    p = pd.read_csv(csv); p = p[(p.design == design) & (p["sub"] == sub) & (p.scenario == scenario)].sort_values("mean_est")
    return p[["delta", "mean_est", "power", "n"]].reset_index(drop=True)


P1_h = power_curve(B2 / "q1_homog_power.csv", "ho9", "homogeneous", "homogeneous")
P1_i = power_curve(B2 / "q1_power.csv", "ho9", "all", "both")
P2_h = power_curve(B2 / "q2_homog_power.csv", "full", "homogeneous", "homogeneous")
P2_i = power_curve(B2 / "q2_power.csv", "full", "all", "both_ramp")
# The earlier analysis's claimed bound: "95% CI within 0.06 SD". A standardized difference d maps to AUC = Phi(d / sqrt 2) (binormal),
# so 0.06 SD ~ delta-AUC 0.017 and 0.03 SD ~ 0.008.
from scipy.stats import norm  # noqa: E402
EARLIER_BOUND = norm.cdf(0.06 / np.sqrt(2)) - 0.5
assert round(EARLIER_BOUND, 3) == 0.017
rows = []
for name, q, p in (("Q1 same effect in every experiment (9-culture design)", "Q1", P1_h), ("Q1 rate-proportional injection, all channels (9-culture design)", "Q1", P1_i),
                   ("Q2 same effect in every experiment", "Q2", P2_h), ("Q2 rate-proportional ramp injection, all channels", "Q2", P2_i)):
    for r in p.itertuples():
        rows.append(dict(question=q, scenario=name, injection_parameter=r.delta, mean_pooled_effect=r.mean_est, detection_rate=r.power, n_repetitions=r.n))
pd.DataFrame(rows).to_csv(OUT / "d_detection_vs_effect.csv", index=False, lineterminator="\n")


NOTE_D = ("Note: sensitivity rests on injected signals only.\nThe biological positive control (Q2) was itself null and the "
          "closed-loop control was not available.")


def draw_detection(fig, spec):
    gs = spec.subgridspec(1, 2, wspace=0.28)
    axes = []
    for k, (q, ph, pi, sesoi, xl, xmax) in enumerate(((Q1, P1_h, P1_i, SESOI_Q1, "Injected effect (Q1, pooled AUC above chance)", 0.135),
                                                       (Q2, P2_h, P2_i, SESOI_Q2, "Injected effect (Q2, pooled growth over sessions)", 0.065))):
        ax = fig.add_subplot(gs[0, k]); axes.append(ax)
        ax.axhline(0.8, color=GRID, lw=1); ax.text(xmax, 0.815, "80%", ha="right", va="bottom", fontsize=7.8, color=MUTED)
        ax.plot(ph.mean_est, ph.power, "-o", color=BLUE, lw=2, ms=5, mec="white", label="same effect in every experiment")
        ax.plot(pi.mean_est, pi.power, color=BLUE, lw=2, ls=(0, (4, 2)), marker="o", ms=5, mec="white", mfc="white", label="effect scaled to each experiment's firing")
        ax.axvline(sesoi, color=INK2, lw=1)
        ax.axvline(abs(q["est"]), color=MUTED, lw=1, ls=(0, (2, 2)))
        ax.text(abs(q["est"]), 1.25, note(f" observed: {q['est']:+.3f}"), fontsize=7.6, color=MUTED, ha="left", va="top")
        if k == 0:
            ax.axvline(EARLIER_BOUND, color=MUTED, lw=1.4)
            ax.text(EARLIER_BOUND, 1.13, note(f" the earlier analysis's reported bound (0.06 SD ≈ {EARLIER_BOUND:.3f})"), fontsize=7.6, color=INK2, va="top", ha="left")
            ax.text(sesoi, 0.30, note(f" ±{sesoi:g}: our 'not\n meaningful' bound"), fontsize=7.6, color=INK2, va="bottom")
        else:
            ax.text(sesoi, 1.13, note(f" ±{sesoi:g}: our 'not meaningful' bound"), fontsize=7.6, color=INK2, va="top")
        ax.set_xlim(0, xmax); ax.set_ylim(0, 1.27); ax.set_yticks([0, 0.25, 0.5, 0.75, 1]); ax.set_yticklabels(["0", "25%", "50%", "75%", "100%"])
        ax.set_xlabel(xl); ax.grid(axis="y", color=GRID, lw=0.7); ax.set_axisbelow(True)
        ax.set_title(["Q1: first exposure (session 1)", "Q2: growth over 100 sessions"][k], loc="left", fontsize=9.5, pad=5)
    axes[0].set_ylabel("Share of test runs that detected the injected effect")
    axes[0].legend(loc="lower right", frameon=False, fontsize=7.6)
    pos = spec.get_position(fig)
    fig.text(pos.x0, pos.y0 - 0.62 / fig.get_figheight(), NOTE_D, fontsize=8, color=INK2, va="top", style="italic")
    fig.text(spec.get_position(fig).x0, spec.get_position(fig).y1 + 0.045, "(d) Would we have seen it? Detection of synthetic effects added to permuted-label data",
             fontweight="bold", fontsize=10.5, color=INK, va="bottom")
    return axes


# ----------------------------------------------------------------------------------------------------------------------
# Paragraphs (plain language, neutral; one or two sentences each).
MDE = dict(q1_h=pd.read_csv(B2 / "q1_homog_mde80.csv").set_index("design").loc["ho9", "mde80_est"],
           q1_i=pd.read_csv(B2 / "q1_mde80.csv").query("design == 'ho9' and subset == 'all' and scenario == 'both'").mde80_est.item(),
           q2_h=pd.read_csv(B2 / "q2_homog_mde80.csv").mde80_est.item(),
           q2_i=pd.read_csv(B2 / "q2_mde80.csv").query("subset == 'all'").mde80_est.item())
assert [round(v, 3) for v in MDE.values()] == [0.036, 0.063, 0.013, 0.050], MDE
PAR = {
 "a": ("The analysis was frozen by a git tag at 16:19, before the held-out run started at 19:06; the GitHub push (19:15) and the "
       "OSF registration (19:51) came during the run, before any output was written (19:58) or displayed (21:13). The recordings "
       "are public and had been analyzed before, so the registration is pre-analysis for this pipeline, not pre-data."),
 "b": (f"Each dot is one held-out experiment ({Q1['n_units']} experiments in {Q1['n_cultures']} cultures) with its 95% interval; the diamond is the "
       f"pooled estimate, {Q1['est']:+.3f} (95% CI {Q1['ci95'][0]:+.3f} to {Q1['ci95'][1]:+.3f}, p = {Q1['randomization_p']:.2f}), inside the pre-set "
       f"±{SESOI_Q1} band, and within the stricter ±{SESOI_Q1_SEC} only narrowly (equivalence uses the 90% CI, upper limit "
       f"{Q1['ci90'][1]:+.3f}; the 95% CI drawn here reaches {Q1['ci95'][1]:+.3f}). Result: not detected in this dataset, and bounded."),
 "c": (f"The same construction for growth over 100 sessions ({Q2['n_units']} experiments in {Q2['n_cultures']} cultures): pooled "
       f"{Q2['est']:+.3f} (95% CI {Q2['ci95'][0]:+.3f} to {Q2['ci95'][1]:+.3f}, p = {Q2['randomization_p']:.2f}), inside the pre-set ±{SESOI_Q2} band. "
       f"Result: not detected in this dataset, and bounded."),
 "d": (f"Synthetic effects of known size were added to development-split data with permuted labels before the held-out run; the pipeline "
       f"found a Q1 effect of about {MDE['q1_h']:.3f} (same in every experiment) or {MDE['q1_i']:.3f} (scaled to firing) 80% of the time, and a Q2 "
       f"growth of about {MDE['q2_h']:.3f} or {MDE['q2_i']:.3f}. The earlier analysis's bound (0.06 SD, about {EARLIER_BOUND:.3f} on this scale) is narrower than our interval "
       f"because it treats trials as independent, while ours accounts for experiments and cultures (Supplementary Information S2); the two numbers answer different questions."),
}

# results.json: every number the brief cites, with its source.
R = []
def rec(key, value, formatted, source, field, label):
    R.append(dict(key=key, label=label, value=value, formatted=formatted, source=source, field=field))
HP_S = "results/D/heldout_primary/summary.json"
for t, lab, where, src in EVENTS:
    rec(f"time_{t:%H%M}", t.strftime("%Y-%m-%d %H:%M:%S PDT"), f"{t:%H:%M}", src.split(" (")[0].split(",")[0], "", lab.replace("\n", " "))
for q, Qd, name in (("q1", Q1, "Q1 first exposure"), ("q2", Q2, "Q2 growth over 100 sessions")):
    rec(f"{q}_n_units", Qd["n_units"], str(Qd["n_units"]), HP_S, f"{q.upper()}.PRIMARY.n_units", f"{name}: experiments")
    rec(f"{q}_n_cultures", Qd["n_cultures"], str(Qd["n_cultures"]), HP_S, f"{q.upper()}.PRIMARY.n_cultures", f"{name}: cultures")
    rec(f"{q}_est", Qd["est"], f"{Qd['est']:+.3f}", HP_S, f"{q.upper()}.PRIMARY.est", f"{name}: pooled estimate")
    rec(f"{q}_ci95_low", Qd["ci95"][0], f"{Qd['ci95'][0]:+.3f}", HP_S, f"{q.upper()}.PRIMARY.ci95[0]", f"{name}: 95% CI lower")
    rec(f"{q}_ci95_high", Qd["ci95"][1], f"{Qd['ci95'][1]:+.3f}", HP_S, f"{q.upper()}.PRIMARY.ci95[1]", f"{name}: 95% CI upper")
    rec(f"{q}_ci90_low", Qd["ci90"][0], f"{Qd['ci90'][0]:+.3f}", HP_S, f"{q.upper()}.PRIMARY.ci90[0]", f"{name}: 90% CI lower (equivalence test)")
    rec(f"{q}_ci90_high", Qd["ci90"][1], f"{Qd['ci90'][1]:+.3f}", HP_S, f"{q.upper()}.PRIMARY.ci90[1]", f"{name}: 90% CI upper (equivalence test)")
    rec(f"{q}_p_rand", Qd["randomization_p"], f"{Qd['randomization_p']:.2f}", HP_S, f"{q.upper()}.PRIMARY.randomization_p", f"{name}: randomization p")
    rec(f"{q}_outcome", Qd["outcome"], Qd["outcome"], HP_S, f"{q.upper()}.PRIMARY.outcome", f"{name}: outcome under the registered rule")
rec("sesoi_q1", SESOI_Q1, f"{SESOI_Q1}", "docs/preregistration_values.json", "SESOI_Q1", "Q1 equivalence bound")
rec("sesoi_q1_secondary", SESOI_Q1_SEC, f"{SESOI_Q1_SEC}", "docs/preregistration_values.json", "SESOI_Q1_SECONDARY", "Q1 secondary (stricter) bound")
rec("sesoi_q2", SESOI_Q2, f"{SESOI_Q2}", "docs/preregistration_values.json", "SESOI_Q2", "Q2 equivalence bound")
rec("q1_tost_equivalent", Q1["tost_equivalent"], "equivalent at ±0.059", HP_S, "Q1.PRIMARY.tost_equivalent", "Q1 TOST at the registered bound")
rec("q1_tost_secondary_equivalent", Q1["tost_secondary_0.03_equivalent"], "equivalent at ±0.03", HP_S, "Q1.PRIMARY.tost_secondary_0.03_equivalent", "Q1 TOST at the secondary bound")
rec("q2_tost_equivalent", Q2["tost_equivalent"], "equivalent at ±0.02", HP_S, "Q2.PRIMARY.tost_equivalent", "Q2 TOST at the registered bound")
rec("mde80_q1_homog_ho9", MDE["q1_h"], f"{MDE['q1_h']:.3f}", "results/B/B2/q1_homog_mde80.csv", "design ho9, mde80_est", "Q1: effect found 80% of the time, same in every experiment, 9-culture design")
rec("mde80_q1_inject_ho9", MDE["q1_i"], f"{MDE['q1_i']:.3f}", "results/B/B2/q1_mde80.csv", "design ho9, subset all, scenario both, mde80_est", "Q1: effect found 80% of the time, injection scaled to firing")
rec("mde80_q2_homog", MDE["q2_h"], f"{MDE['q2_h']:.3f}", "results/B/B2/q2_homog_mde80.csv", "mde80_est", "Q2: growth found 80% of the time, same in every experiment")
rec("mde80_q2_inject", MDE["q2_i"], f"{MDE['q2_i']:.3f}", "results/B/B2/q2_mde80.csv", "subset all, scenario both_ramp, mde80_est", "Q2: growth found 80% of the time, ramp injection scaled to firing")
rec("earlier_bound_sd", 0.06, "0.06 SD", "the earlier analysis", 'its reported bound, "95% CI within 0.06 SD"', "the earlier analysis's claimed bound, in SD units")
rec("earlier_bound_dauc", EARLIER_BOUND, f"{EARLIER_BOUND:.3f}", "tools/make_brief.py", "EARLIER_BOUND = Phi(0.06 / sqrt 2) - 0.5 (binormal AUC)", "the earlier analysis's claimed bound converted to delta-AUC")
rec("verify_script_seconds", 20, "20", "tools/verify_earlier_findings.py", "runtime, about 20 s to 3 min", "Verification script runtime, seconds (about)")
rec("q1_power_curves", "results/B/B2/q1_homog_power.csv (ho9), q1_power.csv (ho9, all, both)", "", "results/B/B2/", "mean_est vs power", "Q1 detection curves in figure (d)")
rec("q2_power_curves", "results/B/B2/q2_homog_power.csv (full), q2_power.csv (full, all, both_ramp)", "", "results/B/B2/", "mean_est vs power", "Q2 detection curves in figure (d)")
rec("dandi_version", "0.260611.0634", "0.260611.0634", "data/manifests/d001611.assets.tsv; scripts/B0_download_001611.py", "VERSION", "DANDI 001611 version analyzed")
rec("dandi_size_gb", 39.93, "40 GB", "data/manifests/d001611.assets.tsv", "sum of size (39,929,261,136 bytes)", "Size of all 2,700 files")
rec("heldout_size_gb", 21.9, "22 GB", "data/manifests/d001611_index.csv + split.csv", "sum of size over held-out experiments (1,500 sessions)", "Size of the held-out sessions")
RESULTS = json.dumps(dict(generated="2026-11-02", by="tools/make_brief.py", from_commit_tag="cp4", numbers=R), indent=1, ensure_ascii=False) + "\n"
for path in (OUT / "results.json", ROOT / "results.json"):
    path.write_bytes(RESULTS.encode("utf-8"))


def put_text(fig, y_top, text, x=0.07, width=0.86, fontsize=9.3, chars=118):
    fig.text(x, y_top, textwrap.fill(text, chars), va="top", ha="left", fontsize=fontsize, color=INK, linespacing=1.38, wrap=False)


# Standalone PNGs (each with its CSV written above).
fig = plt.figure(figsize=(10, 4.0)); draw_timeline(fig, fig.add_gridspec(1, 1, left=0.03, right=0.98, top=0.9, bottom=0.13)[0]); fig.savefig(OUT / "a_timeline.png", dpi=170); plt.close(fig)
fig = plt.figure(figsize=(8.2, 5.6)); draw_forest(fig, fig.add_gridspec(1, 1, left=0.26, right=0.97, top=0.86, bottom=0.11)[0], D1, Q1, "(b) Q1: first exposure, per experiment and pooled", SESOI_Q1, [SESOI_Q1_SEC], "Pre-stimulus prediction of the stimulated source (AUC above the shift null)", "AUC"); fig.savefig(OUT / "b_q1_forest.png", dpi=170); plt.close(fig)
fig = plt.figure(figsize=(8.2, 5.4)); draw_forest(fig, fig.add_gridspec(1, 1, left=0.26, right=0.97, top=0.86, bottom=0.11)[0], D2, Q2, "(c) Q2: growth over 100 sessions, per experiment and pooled", SESOI_Q2, [], "Growth of the prediction across sessions (G above the shift null)", "G"); fig.savefig(OUT / "c_q2_forest.png", dpi=170); plt.close(fig)
fig = plt.figure(figsize=(10, 4.8)); draw_detection(fig, fig.add_gridspec(1, 1, left=0.08, right=0.98, top=0.82, bottom=0.22)[0]); fig.savefig(OUT / "d_detection_vs_effect.png", dpi=170); plt.close(fig)

# Two-page PDF (US Letter).
_ap = argparse.ArgumentParser(add_help=False); _ap.add_argument("--preview", default=None); _ap.add_argument("--check", default=None)
_args = _ap.parse_known_args()[0]; PREVIEW = _args.preview
with PdfPages(OUT / "at_a_glance.pdf") as pdf:
    fig = plt.figure(figsize=(8.5, 11))
    fig.text(0.07, 0.965, "Pre-registered re-analysis of DANDI 001611: at a glance", fontsize=14, fontweight="bold", color=INK, va="top")
    fig.text(0.07, 0.942, "Cedric Cannard and William Reid. From the saved outputs of the held-out run (28 Oct 2026). Each figure's data is attached as CSV.",
             fontsize=8.8, color=INK2, va="top")
    draw_timeline(fig, fig.add_gridspec(1, 1, left=0.05, right=0.96, top=0.905, bottom=0.60)[0])
    put_text(fig, 0.555, PAR["a"])
    draw_forest(fig, fig.add_gridspec(1, 1, left=0.30, right=0.95, top=0.42, bottom=0.135)[0], D1, Q1, "(b) Q1: first exposure, per experiment and pooled", SESOI_Q1, [SESOI_Q1_SEC], "Pre-stimulus prediction of the stimulated source (AUC above the shift null)", "AUC")
    put_text(fig, 0.095, PAR["b"])
    pdf.savefig(fig)
    if PREVIEW: fig.savefig(Path(PREVIEW) / "page1.png", dpi=110)
    plt.close(fig)

    fig = plt.figure(figsize=(8.5, 11))
    draw_forest(fig, fig.add_gridspec(1, 1, left=0.30, right=0.95, top=0.935, bottom=0.665)[0], D2, Q2, "(c) Q2: growth over 100 sessions, per experiment and pooled", SESOI_Q2, [], "Growth of the prediction across sessions (G above the shift null)", "G")
    put_text(fig, 0.625, PAR["c"])
    draw_detection(fig, fig.add_gridspec(1, 1, left=0.09, right=0.96, top=0.47, bottom=0.26)[0])
    put_text(fig, 0.165, PAR["d"])
    fig.text(0.07, 0.045, textwrap.fill("Sources: results/D/heldout_primary/summary.json, forest_q1.csv, forest_q2.csv; results/B/B2/*power*.csv; PROVENANCE.md; Supplementary Information S5-S6 of the paper. "
             "Statements are limited to this dataset and this pipeline; nothing here is a broader claim about the preparation.", 125), fontsize=7.8, color=MUTED, va="top")
    pdf.savefig(fig)
    if PREVIEW: fig.savefig(Path(PREVIEW) / "page2.png", dpi=110)
    plt.close(fig)

(OUT / "paragraphs.txt").write_text("\n\n".join(f"({k}) {v}" for k, v in PAR.items()) + "\n", newline="\n")

# Plain text of the PDF pages (extracted from the PDF itself when pypdf is importable; otherwise from the paragraphs).
try:
    import pypdf
    pages = [pg.extract_text() for pg in pypdf.PdfReader(OUT / "at_a_glance.pdf").pages]
    (OUT / "pdf_text.txt").write_text("\n\n".join(f"===== page {i + 1} =====\n{t}" for i, t in enumerate(pages)) + "\n", newline="\n")
    print("pdf_text.txt extracted with pypdf")
except ImportError:
    pages = None; print("pypdf not importable: pdf_text.txt not written (paragraphs.txt holds the prose)")

if _args.check:
    # Every number cited in the paragraphs and the figure annotations must be a formatted value in
    # results.json (compared without sign, thousands separators or trailing zeros). Clock times (hh:mm) are compared as
    # times. On the extracted PDF pages, which also contain axis tick labels, every token with three or more decimals is
    # checked the same way (cited values carry three decimals; tick labels carry at most two).
    import re
    allowed = {e["formatted"] for e in R if e["formatted"]}
    allowed |= {"2026", "2", "100", "95", "90", "80", "1.96", "001611", "0.06", "28", "0.260611.0634"}  # dates, page, percent and CI conventions, dataset id
    times = {e["formatted"] for e in R if e["key"].startswith("time_")}
    def norm(t):
        t = t.lstrip("+-−±").replace(",", "")
        return t.rstrip("0").rstrip(".") if "." in t else t
    normed = {norm(a) for a in allowed}
    def check(text, min_decimals=0):
        text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", text)  # ISO dates
        found_times = set(re.findall(r"\b\d{1,2}:\d{2}\b", text)); text = re.sub(r"\b\d{1,2}:\d{2}\b", " ", text)
        bad = [t for t in found_times if t not in times and t not in {"16:00", "17:00", "18:00", "19:00", "20:00", "21:00"}]
        toks = set(re.findall(r"(?<![\w.])[+\-−±]?\d[\d,]*(?:\.\d+)?(?![\w.])", text))
        for t in sorted(toks):
            dec = len(t.split(".")[1]) if "." in t else 0
            if dec < min_decimals:
                continue
            if norm(t) not in normed:
                bad.append(t)
        return len(toks) + len(found_times), bad
    body = Path(_args.check).read_text()
    sources = {"external text": (body, 0), "paragraphs": ("\n".join(PAR.values()), 0), "figure annotations": ("\n".join(ANNOT + [NOTE_D]), 0)}
    if pages:
        sources.update({f"pdf page {i + 1} (3-decimal tokens)": (t, 3) for i, t in enumerate(pages)})
    failed = False
    for name, (text, md) in sources.items():
        n, bad = check(text, md)
        failed |= bool(bad)
        print(f"check {name}: {n} tokens, unmatched: {bad}")
    if failed:
        raise SystemExit("number check FAILED")
    print("number check passed: every cited number in the paragraphs, the annotations and the PDF pages is in results.json")

print("written", sorted(p.name for p in OUT.iterdir()))
print("pdf bytes", (OUT / "at_a_glance.pdf").stat().st_size)
