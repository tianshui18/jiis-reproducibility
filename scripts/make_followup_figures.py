"""Data-derived follow-up tables and two journal-style composite plates."""
from __future__ import annotations

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BLUE, GREEN, ORANGE, GRAY, LIGHT = "#386A8D", "#287C72", "#B65C3A", "#55595D", "#E2E5E7"
MODELS = [("Qwen/Qwen3-VL-8B-Instruct", "Qwen3-VL"),
          ("Pro/moonshotai/Kimi-K2.6", "Kimi"), ("gemini-3.8-flash", "Gemini")]


def table(name, headers, rows, alignment):
    lines = [r"\begin{tabular}{" + alignment + "}", r"\toprule",
             " & ".join(headers) + r"\\", r"\midrule"]
    lines += [" & ".join(map(str, row)) + r"\\" for row in rows]
    lines += [r"\bottomrule", r"\end{tabular}"]
    (ROOT / "tables" / (name + ".tex")).write_text("\n".join(lines) + "\n", encoding="utf-8")


def pct(x):
    return f"{100*x:.1f}"


def effect(v):
    return f"{100*v['difference']:+.2f} [{100*v['ci95'][0]:+.2f}, {100*v['ci95'][1]:+.2f}]"


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(ROOT / "figures_revision" / f"{name}.{ext}", bbox_inches="tight", pad_inches=.08, dpi=300)
    plt.close(fig)


def main():
    d = json.loads((ROOT / "analysis/followup_results.json").read_text(encoding="utf-8"))
    old = json.loads((ROOT / "analysis/paper_results.json").read_text(encoding="utf-8"))
    cross = json.loads((ROOT / "analysis/cross_family_summary.json").read_text(encoding="utf-8"))
    agreement = json.loads((ROOT / "analysis/cross_family_agreement.json").read_text(encoding="utf-8"))
    sensitivity = json.loads((ROOT / "analysis/cross_family_sensitivity.json").read_text(encoding="utf-8"))
    audit, order = d["audit"], d["screen"]["order_analysis"]
    nq = [(label, d["nq"]["by_model"][model]["complete"]) for model, label in MODELS]
    rows = []
    for task, cells in order["cells"].items():
        for stratum, v in cells.items():
            rows.append([task, "$C$" if stratum == "stable_correct" else "$R$", v["n"],
                         *[pct(v["accuracy"][c]) for c in ("top_sf", "top_fs", "bottom_sf", "bottom_fs")],
                         effect(v["order_effect"])])
    table("followup_gemini", ["Task", "Stratum", "$N$", "Top SF", "Top FS", "Bottom SF", "Bottom FS", "Effect [95\\% CI]"], rows, "llrrrrrl")
    table("followup_interaction", ["Cohort", "$N_C/N_R$", "$\\Delta_C$", "$\\Delta_R$", "$\\Gamma$ [95\\% CI]"],
          [[task, f"{v['n']['stable_correct']}/{v['n']['support_rescuable']}",
            effect(v["stable_correct"]), effect(v["support_rescuable"]), effect(v["dependency_interaction"])]
           for task, v in {**order["by_dataset"], "Pooled": order["pooled"]}.items()], "lllll")
    table("followup_nq", ["Reader", "$N$", "Base", "Original", "Reverse", "Repair / damage", "Net [95\\% CI]"],
          [[label, v["records"], *[pct(v["accuracy"][c]) for c in ("baseline", "original", "reverse")],
            f"{v['repairs']} / {v['damage']}", effect(v["net_correction"])] for label, v in nq], "lrrrrrl")
    table("followup_nq_full", ["Reader", "Metric", "Base", "Original", "Reverse", "Shuffle 1", "Shuffle 2"],
          [[label, metric, *[pct(v[key][c]) for c in ("baseline", "original", "reverse", "shuffle_1", "shuffle_2")]]
           for label, v in nq for key, metric in (("accuracy", "EM"), ("token_f1", "Token F1"), ("legacy_accuracy", "Legacy EM"))], "llrrrrr")
    table("followup_nq_changes", ["Reader", "Changed", "All wrong", "Mixed", "All correct", "Best saved (\\%)", "Orig.--rev. [95\\% CI]"],
          [[label, v["changed_answers"], v["changed_but_all_wrong"], v["changed_correctness"],
            v["changed_but_all_correct"], pct(v["observed_best_saved_order_accuracy"]), effect(v["original_minus_reverse"])] for label, v in nq], "lrrrrrl")
    tier_a = sensitivity["tier_a_strict"]
    table("followup_audit", ["Scope", "Items", "3/3 agree (\\%)", "Fleiss $\\kappa$", "Gwet AC1"],
          [[label, agreement[key]["items"], pct(agreement[key]["raw_three_of_three_agreement"]),
            f"{agreement[key]['fleiss_kappa']:.3f}", f"{agreement[key]['gwet_ac1']:.3f}"]
           for key, label in (("controlled", "Controlled candidates"), ("natural", "Natural candidates"))], "lrrrr")
    table("followup_audit_stability", ["Judge family", "Valid slots", "Stable pairs", "Position stability (\\%)"],
          [[label, cross["usage"][key]["valid"], cross["model_diagnostics"][key]["stable"],
            pct(cross["model_diagnostics"][key]["position_stability_rate_among_two_valid"])]
           for key, label in (("gpt-6-astra", "GPT"), ("claude-opus-5", "Claude"), ("grok-4.6", "Grok"))], "lrrr")
    table("followup_audit_tiers", ["Scope", "Tier A", "Tier B", "Tier C", "Unresolved", "Tier-A cases"],
          [[label, tiers["tier_a_unanimous"], tiers["tier_b_majority"], tiers["tier_c_two_valid"],
            tiers["unresolved"], f"{cross['case_flow'][key]['tier_a_strict_cases']}/{cross['case_flow'][key]['full_cases']}"]
           for key, label, tiers in (("controlled", "Controlled", cross["candidate_consensus_tiers"]["controlled"]),
                                     ("natural", "Natural", cross["candidate_consensus_tiers"]["natural"]))], "lrrrrl")
    table("followup_strict", ["Stratum / contrast", "Records", "Questions", "Effect [95\\% CI]"],
          [[label, v.get("n", tier_a["controlled_records"]), v["questions"], effect(v)]
           for key, label in (("stable_correct", "$C$"), ("support_rescuable", "$R$"), ("interaction", "$R-C$"))
           for v in [tier_a["controlled_sensitivity"][key]]], "lrrl")
    table("followup_audit_completion", ["Judge family", "Planned slots", "Valid slots", "Invalid / missing"],
          [[label, cross["usage"][key]["slots"], cross["usage"][key]["valid"],
            cross["usage"][key]["slots"] - cross["usage"][key]["valid"]]
           for key, label in (("gpt-6-astra", "GPT"), ("claude-opus-5", "Claude"), ("grok-4.6", "Grok"))]
          + [["Total", cross["inventory"]["planned"], cross["inventory"]["valid"], cross["inventory"]["invalid"]]], "lrrr")
    robust_rows = []
    robust_order = [
        ("tier_a_strict", "Tier A (3/3 stable)"), ("majority", "Majority"), ("two_valid", "Two-valid"),
        ("pair_gpt-6-astra__claude-opus-5", "GPT + Claude"),
        ("pair_gpt-6-astra__grok-4.6", "GPT + Grok"),
        ("pair_claude-opus-5__grok-4.6", "Claude + Grok"),
        ("single_gpt-6-astra", "GPT only"), ("single_claude-opus-5", "Claude only"),
        ("single_grok-4.6", "Grok only"),
    ]
    for key, label in robust_order:
        v = sensitivity[key]
        robust_rows.append([label, v["controlled_cases"], v["controlled_records"],
                            effect(v["controlled_sensitivity"]["interaction"]), v["natural_cases"],
                            effect(v["natural_sensitivity"])])
    table("followup_audit_robustness",
          ["Rule", "Ctrl. cases", "Ctrl. records", "$\\Gamma$ [95\\% CI]", "Natural pairs", "$\\Delta$ [95\\% CI]"],
          robust_rows, "lrrlrl")

    plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 9,
                         "axes.titlesize": 10, "axes.labelsize": 9, "xtick.labelsize": 8.5,
                         "ytick.labelsize": 8.5, "axes.linewidth": .65, "pdf.fonttype": 42,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig = plt.figure(figsize=(7.25, 5.65), layout="constrained")
    gs = fig.add_gridspec(2, 2)
    ax = fig.add_subplot(gs[0, 0])
    ax.set_title("(a) Cross-family agreement", loc="left", pad=10)
    metrics = [("3/3", "raw_three_of_three_agreement", BLUE), ("Fleiss $\\kappa$", "fleiss_kappa", GREEN), ("Gwet AC1", "gwet_ac1", ORANGE)]
    x = np.arange(2); width = .23
    for j, (label, key, color) in enumerate(metrics):
        vals = [agreement[s][key] for s in ("controlled", "natural")]
        ax.bar(x + (j-1)*width, vals, width=width, color=color, label=label)
    ax.set(xticks=x, xticklabels=["Controlled", "Natural"], ylim=(0, 1.03), ylabel="Agreement coefficient")
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower left", handlelength=1, columnspacing=.7)
    ax = fig.add_subplot(gs[0, 1])
    ax.set_title("(b) Original/swapped stability", loc="left", pad=10)
    judges = ["gpt-6-astra", "claude-opus-5", "grok-4.6"]
    vals = [100*cross["model_diagnostics"][j]["position_stability_rate_among_two_valid"] for j in judges]
    ax.bar(range(3), vals, color=(BLUE, GREEN, ORANGE), width=.62)
    for i, v in enumerate(vals): ax.text(i, v+.25, f"{v:.2f}", ha="center", fontsize=8.5)
    ax.set(xticks=range(3), xticklabels=["GPT", "Claude", "Grok"], ylim=(88, 98), ylabel="Stable candidate labels (%)")
    ax = fig.add_subplot(gs[1, 0])
    ax.set_title("(c) Effect after semantic filtering", loc="left", pad=10)
    foil = audit["foil"]
    comparisons = (("Full sample", old["controlled"]["primary"], BLUE, "o"),
                   ("Earlier Sol strict", foil["controlled_sensitivity"], GRAY, "^"),
                   ("Three-family Tier A", tier_a["controlled_sensitivity"], GREEN, "s"))
    for j, (name, v, color, marker) in enumerate(comparisons):
        vals = [100*v[s]["difference"] for s in ("stable_correct", "support_rescuable")]
        ax.plot([0, 1], vals, marker=marker, color=color, label=name, lw=1.1)
        for x, y in enumerate(vals):
            offsets = (((-8, -20), (-8, -18)), ((18, -2), (0, 3)), ((0, 14), (0, 10)))
            ax.annotate(f"{y:.2f}", (x, y), xytext=offsets[j][x], textcoords="offset points", ha="center", color=color, fontsize=8)
    ax.set(xticks=[0, 1], xticklabels=["Stable-correct", "Support-rescuable"], xlim=(-.25, 1.25), ylim=(-.5, 19), ylabel="Support-first effect (pp)")
    ax.legend(frameon=False, loc="upper left", fontsize=7.5)
    ax = fig.add_subplot(gs[1, 1])
    ax.set_title("(d) Strict Tier-A retention", loc="left", pad=10)
    full = [cross["case_flow"][s]["full_cases"] for s in ("controlled", "natural")]
    kept = [cross["case_flow"][s]["tier_a_strict_cases"] for s in ("controlled", "natural")]
    y = np.arange(2)
    ax.barh(y, full, color=LIGHT, height=.55, label="Not retained")
    ax.barh(y, kept, color=GREEN, height=.55, label="Tier A")
    for i, (k, n) in enumerate(zip(kept, full)):
        ax.text(k+max(full)*.015, i, f"{k}/{n} ({100*k/n:.1f}%)", va="center", fontsize=8.5)
    ax.set(yticks=y, yticklabels=["Controlled", "Natural"], xlim=(0, 690), xlabel="Cases / conflict pairs")
    ax.invert_yaxis()
    save(fig, "fig08_audit")

    fig = plt.figure(figsize=(7.25, 5.5), layout="constrained")
    gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1])
    ax = fig.add_subplot(gs[0, 0])
    ax.set_title("(a) Original retrieval: repair and damage", loc="left", pad=10)
    for i, (label, v) in enumerate(nq):
        repair, damage = 100*v["repairs"]/v["records"], 100*v["damage"]/v["records"]
        ax.barh(i, repair, height=.55, color=GREEN)
        ax.barh(i, -damage, height=.55, color=ORANGE)
        ax.text(repair+.7, i, f"{v['repairs']} / {v['damage']}", va="center", fontsize=9)
    ax.axvline(0, color=GRAY, lw=.6)
    ax.set(yticks=range(3), yticklabels=[n for n, _ in nq], xlim=(-11,32), xlabel="Share of complete records (%)")
    ax.invert_yaxis()
    ax = fig.add_subplot(gs[0, 1])
    ax.set_title("(b) Accuracy across retrieval orders", loc="left", pad=10)
    for (label, v), color, marker in zip(nq, (BLUE, GREEN, ORANGE), ("o", "s", "^")):
        ax.plot(range(5), [100*v["accuracy"][c] for c in ("baseline", "original", "reverse", "shuffle_1", "shuffle_2")], color=color, marker=marker, ms=4, lw=1, label=label)
    ax.set(xticks=range(5), xticklabels=["Base", "Orig.", "Rev.", "Sh. 1", "Sh. 2"], ylim=(17,51), ylabel="Exact match (%)")
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower right", handlelength=1, columnspacing=.7)
    ax = fig.add_subplot(gs[1, :])
    ax.set_title("(c) Changed answers: most remain wrong in every evidence order", loc="left", pad=10)
    for i, (label, v) in enumerate(nq):
        left = 0
        for key, color in (("changed_but_all_wrong", GRAY), ("changed_correctness", GREEN), ("changed_but_all_correct", BLUE)):
            n = v[key]
            ax.barh(i, n, left=left, color=color, height=.55)
            if n >= 5: ax.text(left+n/2, i, str(n), ha="center", va="center", color="white")
            left += n
        ax.text(left+1, i, f"{left}/{v['records']}", va="center", fontsize=9)
    ax.set(yticks=range(3), yticklabels=[n for n, _ in nq], xlim=(0,105), xlabel="Changed records / complete records (unchanged omitted)")
    ax.invert_yaxis()
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=l) for c, l in ((GRAY,"All wrong"),(GREEN,"Correctness changes"),(BLUE,"All correct"))], frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(.5,-.57), fontsize=8)
    save(fig, "fig09_nq")


if __name__ == "__main__":
    main()
