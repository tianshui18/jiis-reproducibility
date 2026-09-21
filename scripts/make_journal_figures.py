"""Journal-sized vector plates: compact design matrix and reader-resolved results."""
from __future__ import annotations

import json

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
import numpy as np

import make_revision_figures as base

ROOT, D, R = base.ROOT, base.D, base.R
C = json.loads((ROOT / "analysis/model_coverage.json").read_text(encoding="utf-8"))
BLUE, GREEN, ORANGE, GRAY, LIGHT = "#386A8D", "#287C72", "#B65C3A", "#55595D", "#E2E5E7"
base.BLUE, base.GREEN, base.ORANGE, base.GRAY, base.LIGHT = BLUE, GREEN, ORANGE, GRAY, LIGHT
base.SHORT = ["Qwen3-VL-8B", "Qwen3.5-9B", "Kimi-K2.6", "GLM-4.5V", "Gemini 3.8"]
base.CMAP = LinearSegmentedColormap.from_list("journal_signed", [ORANGE, "#FCFCFC", BLUE])
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 9,
                     "axes.titlesize": 10, "axes.labelsize": 9, "xtick.labelsize": 8.5,
                     "ytick.labelsize": 8.5, "axes.linewidth": .65, "lines.linewidth": 1,
                     "xtick.major.width": .6, "ytick.major.width": .6})
TITLES = {
    "A  Dependence differs by reader": "(a) Within-reader stratum contrast",
    "B  Interaction by task and reader": "(b) Task-specific interaction",
    "A  Perturbation response (pp)": "(a) Wording and distractor perturbations",
    "B  No monotone distraction law": "(b) Distractor response",
    "D  Answer changes are not necessarily changes in correctness": "(d) Decomposition of answer variability",
    "A  Conflicts are unevenly available": "(a) Candidate-set composition",
    "B  What a support/foil swap changes": "(b) Directional conflict swaps",
    "C  Opposing changes cancel": "(c) Original versus reversed retrieval",
    "D  Observed order headroom": "(d) Observed four-order envelope",
    "A  Four-condition signatures separate fragility from persistent failure": "(a) Joint response distribution",
    "B  Persistence after adding conflict": "(b) Correctness regimes",
    "C  Aggregation outcomes": "(c) Aggregation outcomes",
}


def title(ax, text):
    if text in TITLES:
        text = TITLES[text]
    elif len(text) > 3 and text[1:3] == "  ":
        text = "(" + text[0].lower() + ") " + text[3:]
    ax.set_title(text, loc="left", fontweight="normal", pad=10)


base.title = title


def design():
    fig = plt.figure(figsize=(7.25, 5.15), layout="constrained")
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.35], height_ratios=[1.15, 1])
    ax = fig.add_subplot(gs[0, 0]); ax.axis("off"); ax.set(xlim=(0, 1), ylim=(0, 1))
    title(ax, "(a) Independently screened strata")
    ax.text(.5, .94, r"$q \in Q,\; m \in M$", ha="center", fontsize=12)
    ax.text(.5, .85, "400 questions; five reader endpoints", ha="center", fontsize=8.5)
    ax.annotate("", (.5, .67), (.5, .79), arrowprops={"arrowstyle": "->", "lw": .8, "color": GRAY})
    ax.text(.5, .6, r"No-evidence outcomes: $\mathbf{y}^{0}_{qm}$", ha="center", fontsize=10)
    for x in (.21, .79):
        ax.annotate("", (x, .36), (.5, .53), arrowprops={"arrowstyle": "->", "lw": .8, "color": GRAY})
    ax.text(.19, .29, r"$\mathbf{y}^{0}_{qm}=(1,1,1)$", ha="center", color=BLUE, fontsize=10)
    ax.text(.80, .29, r"$\mathbf{y}^{0}_{qm}=(0,0,0)$", ha="center", color=GREEN, fontsize=10)
    ax.text(.80, .18, r"Support-only: $Y^{S}_{qm}=1$", ha="center", color=GREEN, fontsize=9)
    ax.text(.19, .035, r"$C$: stable-correct" + "\n515 records", ha="center", va="center", fontsize=9)
    ax.text(.80, .035, r"$R$: support-rescuable" + "\n637 records", ha="center", va="center", fontsize=9)
    ax = fig.add_subplot(gs[0, 1]); ax.axis("off"); ax.set(xlim=(-2.6, 5.9), ylim=(-.9, 4.7))
    title(ax, "(b) Fixed-content intervention matrix")
    for j in range(5): ax.text(j+.5, 4.2, str(j+1), ha="center", fontsize=9)
    ax.text(-.25, 4.2, "Slot", ha="right", fontsize=9)
    orders = [("Top, SF", "SFNNN"), ("Top, FS", "FSNNN"), ("Bottom, SF", "NNNSF"), ("Bottom, FS", "NNNFS")]
    for i, (label, roles) in enumerate(orders):
        y = 3.2-i*.88
        ax.text(-.28, y+.28, label, ha="right", va="center", fontsize=9)
        n = 0
        for j, role in enumerate(roles):
            if role == "N": n += 1
            color = GREEN if role == "S" else ORANGE if role == "F" else LIGHT
            ax.add_patch(Rectangle((j+.04, y), .92, .56, facecolor=color, edgecolor="white", lw=.5))
            ax.text(j+.5, y+.28, role if role != "N" else f"$N_{n}$", ha="center", va="center", fontsize=10, color="white" if role != "N" else GRAY)
    ax.plot([-.15,5.08],[1.99,1.99],color=GRAY,lw=.5)
    ax.text(2.5, -.4, r"$S$: support    $F$: foil    $N$: neutral", ha="center", fontsize=8.5)
    ax = fig.add_subplot(gs[1, :]); ax.axis("off"); ax.set(xlim=(0, 1), ylim=(0, 1))
    title(ax, "(c) Endpoint coverage across experimental stages")
    xs = [.015, .38, .59, .79, .95]
    headers = ["Reader", "Controlled\n4 tasks", "Natural\n3 tasks", "Robustness\n4 tasks", "Ranking\n3 tasks"]
    for x, label in zip(xs, headers): ax.text(x, .89, label, ha="left" if x==xs[0] else "center", va="center", fontsize=9)
    ax.plot([0,1],[.985,.985],color="black",lw=.8); ax.plot([0,1],[.785,.785],color="black",lw=.55)
    for i, (model, label) in enumerate(zip(base.MODELS, base.SHORT)):
        ctrl = D["controlled"]["by_model"][model]
        nctrl = sum(ctrl[s]["n"] for s in base.STRATA)
        nnat = sum(R["natural"]["cells"][t][model]["n"] for t in ("BoolQ", "InfoSeek", "StrategyQA"))
        ranking = C["ranking_common_by_reader"].get(model)
        values = [label, str(nctrl), str(nnat), "40" if model in base.MODELS[:4] else "Not run", str(ranking["original"]["n"]) if ranking else "Not run"]
        y = .68-i*.127
        for j, (x, value) in enumerate(zip(xs, values)):
            ax.text(x, y, value, ha="left" if j==0 else "center", va="center", fontsize=9, color=BLUE if i==4 else "#222222")
    ax.plot([0,1],[.085,.085],color="black",lw=.8)
    ax.text(0,-.045,"Complete question-reader records; ranking uses the common set. Columns reuse questions.",fontsize=8)
    base.save(fig, "fig01_design")


def mitigation():
    fig = plt.figure(figsize=(7.25, 5.45), layout="constrained")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], height_ratios=[1,1])
    ax = fig.add_subplot(gs[:,0])
    readers = [base.MODELS[0], base.MODELS[-1]]
    methods = ["original", "random", "reverse", "cross_encoder", "llm_reranker", "permutation_vote", "budget_matched_self_consistency", "credibility"]
    matrix, accuracy = [], []
    for method in methods:
        vals = [C["ranking_common_by_reader"][m][method] for m in readers]
        a = [v["accuracy"]*100 for v in vals] + [R["ranking"]["common_complete"][method]["accuracy"]*100]
        delta = [v["vs_original"]["difference"]*100 for v in vals] + [R["ranking"]["common_complete"][method]["vs_original"]["net"]*100]
        matrix.append(delta); accuracy.append(a)
    im = ax.imshow(matrix, cmap=base.CMAP, vmin=-2.5, vmax=2.5, aspect="auto")
    for (i,j), value in np.ndenumerate(np.array(accuracy)):
        ax.text(j,i,f"{value:.1f}\n({matrix[i][j]:+.1f})",ha="center",va="center",fontsize=8.5,color="white" if abs(matrix[i][j])>1.75 else "#222222")
    labels = ["Original", "Shuffle", "Reverse", "Cross-encoder", "LLM relevance", "Four-order vote", "Repeated original", "Credibility"]
    ax.set_yticks(range(8), labels); ax.set_xticks(range(3),["Qwen3-VL\nN = 300", "Gemini 3.8\nN = 291", "Pooled\nN = 591"])
    ax.tick_params(length=0); ax.spines[["left","bottom"]].set_visible(False)
    title(ax,"(a) Reader-specific answer accuracy")
    cax=ax.inset_axes([0,-.17,1,.025])
    cb=fig.colorbar(im,cax=cax,orientation="horizontal")
    cb.set_label("Change from original order (pp)"); cb.set_ticks([-2,0,2])
    ax=fig.add_subplot(gs[0,1])
    for method,label,color,style in zip(("cross_encoder","llm_reranker","credibility"),("Cross-encoder","LLM relevance","Credibility"),(GRAY,BLUE,ORANGE),(":","--","-")):
        values=np.array(R["ranking"]["permutations"][method]["inversions"])
        xs=np.arange(16); ys=np.array([(values<=x).mean()*100 for x in xs])
        ax.step(xs,ys,where="post",label=label,color=color,ls=style,lw=1.3)
        ax.scatter([0],[ys[0]],color=color,s=10,zorder=3)
    ax.set(xlim=(-.3,15.3),ylim=(0,103),xticks=[0,5,10,15],yticks=[0,25,50,75,100],xlabel="Inverted pairs (out of 15)",ylabel="Cumulative candidate sets (%)")
    ax.legend(frameon=False,fontsize=8,loc="lower right")
    title(ax,"(b) Ranking displacement")
    ax=fig.add_subplot(gs[1,1])
    labels=["Cross-encoder","LLM relevance","Credibility"]
    for i,method in enumerate(("cross_encoder","llm_reranker","credibility")):
        v=R["ranking"]["permutations"][method]; nums=[v["n"]-v["unchanged"],v["unchanged"]-v["fallback"],v["fallback"]]
        left=0
        for n,color in zip(nums,(GREEN,LIGHT,ORANGE)):
            ax.barh(i,n,left=left,height=.48,color=color,edgecolor="white",linewidth=.3)
            if n>=15: ax.text(left+n/2,i,str(n),ha="center",va="center",color="white" if color!=LIGHT else "black",fontsize=8.5)
            left+=n
    ax.set_yticks(range(3),labels); ax.invert_yaxis(); ax.set(xlim=(0,300),xticks=[0,100,200,300],xlabel="Candidate sets (N = 300)")
    handles=[Rectangle((0,0),1,1,color=c) for c in (GREEN,LIGHT,ORANGE)]
    ax.legend(handles,["Changed", "Valid, unchanged", "Fallback"],frameon=False,fontsize=8,loc="upper left",bbox_to_anchor=(-.02,-.3),ncol=1)
    title(ax,"(c) Ranking execution")
    base.save(fig,"fig06_mitigation")


def main():
    for fn in (design, base.controlled, base.robustness, base.natural, base.conflicts, mitigation, base.diagnostics, base.graphical):
        fn()
    print("Rendered seven journal-style composite plates and graphical abstract.")


if __name__ == "__main__":
    main()
