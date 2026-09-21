"""Seven complementary multi-panel figures; shared typography and semantic colors."""
from __future__ import annotations

import json
import itertools
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "analysis/paper_results.json").read_text(encoding="utf-8"))
R = json.loads((ROOT / "analysis/revision_diagnostics.json").read_text(encoding="utf-8"))
OUT = ROOT / "figures_revision"
BLUE, GREEN, ORANGE, GRAY, LIGHT = "#0072B2", "#009E73", "#D55E00", "#62686D", "#DCE1E4"
MODELS = ["Qwen/Qwen3-VL-8B-Instruct", "Qwen/Qwen3.5-9B", "Pro/moonshotai/Kimi-K2.6", "zai-org/GLM-4.5V", "gemini-3.8-flash"]
SHORT = ["Qwen3-VL", "Qwen3.5", "Kimi", "GLM", "Gateway"]
TASKS = ["BoolQ", "InfoSeek", "OVEN-MTEB", "StrategyQA"]
STRATA = ["stable_correct", "support_rescuable"]
METHODS = ["original", "random", "reverse", "cross_encoder", "llm_reranker", "permutation_vote", "budget_matched_self_consistency", "credibility"]
LABELS = ["Original", "Shuffle", "Reverse", "Cross-encoder", "LLM relevance", "Four-order vote", "Repeated original (2)", "Credibility"]
CMAP = LinearSegmentedColormap.from_list("signed", [ORANGE, "#FFFFFF", BLUE])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 10, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8, "pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300})


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", pad_inches=.08)
    plt.close(fig)


def title(ax, text):
    ax.set_title(text, loc="left", fontweight="bold", pad=12)


def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11, lw=1, color=GRAY))


def box(ax, x, y, w, h, text, color=GRAY, size=8):
    ax.add_patch(Rectangle((x, y), w, h, facecolor="white", edgecolor=color, lw=.9))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=size, linespacing=1.5, color=color)


def design():
    fig = plt.figure(figsize=(7.25, 5.8), layout="constrained")
    gs = fig.add_gridspec(3, 1, height_ratios=[1.3, 1.15, .9])
    ax = fig.add_subplot(gs[0]); ax.axis("off"); ax.set(xlim=(0, 100), ylim=(0, 100))
    title(ax, "A  Screening selects a model-question state, not a task label")
    box(ax, 0, 36, 22, 33, "400 questions\n4 tasks x 5 endpoints")
    arrow(ax, (22, 52), (29, 52))
    box(ax, 29, 36, 24, 33, "Three separate\nno-evidence calls")
    arrow(ax, (53, 56), (63, 80)); arrow(ax, (53, 48), (63, 26))
    box(ax, 63, 66, 36, 30, "3/3 correct: stable-correct\n515 complete records", BLUE)
    box(ax, 63, 7, 36, 42, "0/3 correct + support-only success\nSupport-rescuable\n637 complete records", GREEN)
    ax.text(0, 12, "Mixed or unrescued outcomes are excluded; cells are capped at 40.", fontsize=8, color=GRAY)
    ax = fig.add_subplot(gs[1]); ax.axis("off"); ax.set(xlim=(0, 100), ylim=(0, 100))
    title(ax, "B  A crossed intervention separates pair order from pair location")
    orders = [("Top / SF", "SFNNN"), ("Top / FS", "FSNNN"), ("Bottom / SF", "NNNSF"), ("Bottom / FS", "NNNFS")]
    for i, (label, order) in enumerate(orders):
        x, y = (0 if i < 2 else 51), (64 if i % 2 == 0 else 22)
        ax.text(x, y+10, label, va="center", fontsize=8)
        for j, role in enumerate(order):
            bx = x+19+j*5.4
            box(ax, bx, y, 4.8, 22, role, {"S": GREEN, "F": ORANGE, "N": GRAY}[role])
    ax.text(0, -2, "Content, reference IDs and image are fixed within each record.", color=GRAY, fontsize=8)
    ax = fig.add_subplot(gs[2]); ax.axis("off"); ax.set(xlim=(0, 100), ylim=(0, 100))
    title(ax, "C  Two natural comparisons answer different questions")
    box(ax, 0, 27, 44, 47, "Unselected cohort: 600 questions\nOriginal / reverse / two shuffles", BLUE)
    box(ax, 56, 27, 43, 47, "Labeled conflicts: 70 questions\nSwap support and foil only", GREEN)
    ax.text(0, 4, "S: answer-bearing support     F: scorer-defined foil     N: neutral reference", color=GRAY, fontsize=8)
    save(fig, "fig01_design")


def controlled():
    fig, axs = plt.subplots(1, 2, figsize=(7.25, 3.7), gridspec_kw={"width_ratios": [1, 1.5]}, layout="constrained")
    ax = axs[0]
    for i, m in enumerate(MODELS):
        v = D["controlled"]["by_model"][m]
        xs = [v[s]["difference"]*100 for s in STRATA]
        ax.plot(xs, [i, i], color=LIGHT, lw=3, zorder=1)
        ax.scatter(xs, [i, i], color=[BLUE, GREEN], s=36, zorder=2)
    ax.scatter([], [], color=BLUE, label="Stable-correct"); ax.scatter([], [], color=GREEN, label="Support-rescuable")
    ax.set_yticks(range(5), SHORT); ax.invert_yaxis(); ax.axvline(0, color=GRAY, lw=.6)
    ax.set(xlabel="Support-first advantage (pp)", xlim=(-5, 38))
    ax.legend(loc="lower right", frameon=False, fontsize=7)
    title(ax, "A  Dependence differs by reader")
    matrix = []
    for m in MODELS:
        row = []
        for d in TASKS:
            c = R["controlled"]["cells"][m][d]
            row.append(100*(c[STRATA[1]]["swaps"]["net"] - c[STRATA[0]]["swaps"]["net"]))
        matrix.append(row)
    ax = axs[1]; im = ax.imshow(matrix, cmap=CMAP, vmin=-50, vmax=50, aspect="auto")
    for i, m in enumerate(MODELS):
        for j, ds in enumerate(TASKS):
            c = R["controlled"]["cells"][m][ds]
            ax.text(j, i, f"{matrix[i][j]:+.1f}\n{c[STRATA[0]]['n']}/{c[STRATA[1]]['n']}", ha="center", va="center", fontsize=7.5, color="white" if abs(matrix[i][j])>33 else "#222222")
    ax.set_xticks(range(4), ["BoolQ", "InfoSeek", "OVEN", "StrategyQA"], rotation=25, ha="right")
    ax.set_yticks(range(5), SHORT); ax.tick_params(length=0)
    title(ax, "B  Interaction by task and reader")
    fig.colorbar(im, ax=ax, shrink=.65, label="Interaction (pp)", pad=.03)
    ax.set_xlabel("Cell labels: interaction / counts C and R")
    save(fig, "fig02_controlled")


def robustness():
    keys = ["original", "paraphrase_1", "paraphrase_2", "length_matched", "distractor_0", "distractor_2", "distractor_4"]
    labels = ["Original", "Paraphrase 1", "Paraphrase 2", "Word matched", "0 distractors", "2 distractors", "4 distractors"]
    fig, axs = plt.subplots(1, 2, figsize=(7.25, 3.8), gridspec_kw={"width_ratios": [1.5, 1]}, layout="constrained")
    mat = np.array([[D["mechanism"]["by_model"][m][k]["difference"]*100 for m in MODELS[:4]]+[D["mechanism"]["pooled"][k]["difference"]*100] for k in keys])
    ax = axs[0]; ax.imshow(mat, cmap=CMAP, vmin=-50, vmax=50, aspect="auto")
    for (i, j), v in np.ndenumerate(mat): ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=8, color="white" if abs(v)>33 else "#222222")
    ax.set_xticks(range(5), SHORT[:4]+["Pooled"], rotation=30, ha="right"); ax.set_yticks(range(7), labels); ax.tick_params(length=0)
    title(ax, "A  Perturbation response (pp)")
    ax = axs[1]
    for i, m in enumerate(MODELS[:4]):
        ys = [100*D["mechanism"]["by_model"][m][f"distractor_{n}"]["difference"] for n in (0, 2, 4)]
        ax.plot([0, 2, 4], ys, marker=["o", "s", "^", "D"][i], ms=4, color=[BLUE, GREEN, ORANGE, GRAY][i], label=SHORT[i], lw=1.2)
    ax.axhline(0, color=GRAY, lw=.6); ax.set(xticks=[0, 2, 4], xlabel="Neutral distractors", ylabel="Support-first advantage (pp)", ylim=(-5, 38))
    ax.legend(frameon=False, fontsize=7, loc="upper right"); title(ax, "B  No monotone distraction law")
    save(fig, "fig03_robustness")


def natural():
    fig = plt.figure(figsize=(7.25, 5.9), layout="constrained")
    gs = fig.add_gridspec(2, 3, height_ratios=[1.35, 1])
    for j, ds in enumerate(("BoolQ", "InfoSeek", "StrategyQA")):
        ax = fig.add_subplot(gs[0, j])
        for i, m in enumerate(MODELS):
            t = R["natural"]["cells"][ds][m]["transition"]
            ax.barh(i, 100*t["counts"]["01"]/t["n"], color=GREEN, height=.62)
            ax.barh(i, -100*t["counts"]["10"]/t["n"], color=ORANGE, height=.62)
        ax.axvline(0, color=GRAY, lw=.6); ax.set_yticks(range(5), SHORT if j==0 else [""]*5); ax.invert_yaxis()
        ax.set(xlim=(-15, 30), xlabel="Damage (-) / correction (+), %")
        title(ax, f"{chr(65+j)}  {ds}")
    ax = fig.add_subplot(gs[1, :])
    for i, ds in enumerate(("BoolQ", "InfoSeek", "StrategyQA")):
        row = R["natural"]["tasks"][ds]; left = 0
        for key, color in (("correctness_changes", BLUE), ("wrong_strings_change", ORANGE), ("correct_strings_change", GREEN)):
            val = row["categories"][key]/row["n"]*100
            ax.barh(i, val, left=left, color=color, height=.58)
            if val>2: ax.text(left+val/2, i, f"{val:.1f}", ha="center", va="center", color="white", fontsize=8)
            left += val
        ax.text(left+.8, i, f"{sum(v for k,v in row['categories'].items() if k!='invariant')}/{row['n']}", va="center", fontsize=8)
    ax.set_yticks(range(3), ["BoolQ", "InfoSeek", "StrategyQA"]); ax.invert_yaxis(); ax.set(xlim=(0, 50), xlabel="Records with changing answer strings (%)")
    handles = [Rectangle((0,0),1,1,color=c) for c in (BLUE, ORANGE, GREEN)]
    ax.legend(handles, ["Correctness changes", "All four answers wrong", "All four answers correct"], frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5,-.24), fontsize=7.5)
    title(ax, "D  Answer changes are not necessarily changes in correctness")
    save(fig, "fig04_natural")


def conflicts():
    tasks = ("BoolQ", "InfoSeek", "StrategyQA")
    fig, axs = plt.subplots(2, 2, figsize=(7.25, 5.0), layout="constrained")
    ax = axs[0,0]
    for i, ds in enumerate(tasks):
        v = R["natural"]["candidate_coverage"][ds]; left=0
        for key, color in (("conflict", ORANGE), ("support_only", GREEN), ("no_support", LIGHT), ("invalid_labels", GRAY)):
            val=v["counts"].get(key,0)/v["n"]*100; ax.barh(i,val,left=left,color=color,height=.58); left+=val
        ax.text(102,i,f"{v['counts'].get('conflict',0)}/{v['n']}",va="center",fontsize=8)
    ax.set_yticks(range(3),tasks); ax.invert_yaxis(); ax.set(xlim=(0,122),xticks=[0,50,100],xlabel="Candidate sets (%); conflict count at right")
    title(ax,"A  Conflicts are unevenly available")
    ax=axs[0,1]
    for i, ds in enumerate(tasks):
        t=R["natural"]["conflict_pairs"][ds]
        ax.bar(i-.17,t["counts"]["01"],width=.32,color=GREEN); ax.bar(i+.17,t["counts"]["10"],width=.32,color=ORANGE)
        ax.text(i,max(t["counts"]["01"],t["counts"]["10"])+.5,f"N={t['n']}",ha="center",fontsize=7)
    ax.set(xticks=range(3),xticklabels=tasks,ylabel="Discordant model-record pairs",ylim=(0,25)); ax.tick_params(axis="x",rotation=15)
    ax.legend(["SF repairs", "SF damages"],frameon=False,fontsize=7)
    title(ax,"B  What a support/foil swap changes")
    ax=axs[1,0]
    for i,ds in enumerate(tasks):
        t=R["natural"]["tasks"][ds]["original_reverse"]
        ax.barh(i,100*t["counts"]["01"]/t["n"],color=GREEN,height=.55)
        ax.barh(i,-100*t["counts"]["10"]/t["n"],color=ORANGE,height=.55)
        ax.scatter(100*t["net"],i,marker="D",s=28,color="#222222",zorder=3)
    ax.axvline(0,color=GRAY,lw=.6); ax.set_yticks(range(3),tasks); ax.invert_yaxis(); ax.set(xlim=(-4,4),xlabel="Original versus reverse: change (%)")
    title(ax,"C  Opposing changes cancel")
    ax=axs[1,1]
    for i,ds in enumerate(tasks):
        v=R["natural"]["tasks"][ds]
        lo,hi=100*v["observed_worst"],100*v["observed_best"]
        ax.plot([lo,hi],[i,i],lw=8,color=LIGHT,solid_capstyle="butt")
        ax.scatter(100*v["original_accuracy"],i,color=BLUE,s=35,zorder=3)
        ax.text(hi+1.5,i,f"+{hi-100*v['original_accuracy']:.1f}",va="center",fontsize=8)
    ax.set_yticks(range(3),tasks); ax.invert_yaxis(); ax.set(xlim=(10,100),xlabel="Observed worst / original / best (%)")
    title(ax,"D  Observed order headroom")
    save(fig,"fig05_conflicts")


def mitigation():
    fig=plt.figure(figsize=(7.25,5.65),layout="constrained")
    gs=fig.add_gridspec(2,2,height_ratios=[1.1,1])
    ax=fig.add_subplot(gs[0,0])
    common=R["ranking"]["common_complete"]
    for i,k in enumerate(METHODS):
        x=common[k]["answer_calls"]/common[k]["n"]; y=common[k]["accuracy"]*100
        ax.scatter(x,y,color=ORANGE if k=="credibility" else BLUE,s=30)
        dx,dy={0:(8,5),1:(8,-7),2:(8,-10),3:(8,0),4:(8,8),5:(-83,5),6:(-44,12),7:(8,-20)}[i]
        ax.annotate(str(i+1), (x,y), xytext=(dx,dy),textcoords="offset points",fontsize=8,arrowprops={"arrowstyle":"-","lw":.5,"color":GRAY})
    ax.set(xlim=(.8,4.4),ylim=(57.6,60.2),xticks=[1,2,3,4],xlabel="Answer calls per record",ylabel="Common-set accuracy (%)")
    title(ax,"A  More calls do not ensure a gain")
    ax=fig.add_subplot(gs[0,1]); ax.axis("off")
    title(ax,"B  Ranking validity and overhead")
    for i,(k,label) in enumerate(zip(("cross_encoder","llm_reranker","credibility"),("Cross-encoder","LLM relevance","Credibility"))):
        row=R["ranking"]["permutations"][k]; y=.82-i*.28
        ax.text(0,y,label,weight="bold",fontsize=8.5)
        ax.text(0,y-.1,f"{300-row['fallback']}/300 valid; {row['unchanged']} unchanged",fontsize=8)
        tokens=D["reranking"]["ranking"].get(k+"_tokens")
        ax.text(0,y-.19,f"{tokens:,} recorded ranking tokens" if tokens else "300 cross-encoder calls; tokens not pooled",fontsize=7.5,color=GRAY)
    ax=fig.add_subplot(gs[1,0])
    for i,(k,label,color) in enumerate(zip(("cross_encoder","llm_reranker","credibility"),("Cross-encoder","LLM relevance","Credibility"),(BLUE,GRAY,ORANGE))):
        values=np.array(R["ranking"]["permutations"][k]["inversions"])/15
        bins=[0,.001,1/3+1e-4,2/3+1e-4,1.001]; counts=np.histogram(values,bins=bins)[0]
        left=0
        for j,n in enumerate(counts):
            ax.barh(i,n,left=left,color=[LIGHT,"#B5D9ED",BLUE,"#00496F"][j],height=.56)
            if n>18: ax.text(left+n/2,i,str(n),ha="center",va="center",color="white" if j>1 else "#222222",fontsize=8)
            left+=n
    ax.set_yticks(range(3),["Cross-encoder","LLM relevance","Credibility"]); ax.invert_yaxis(); ax.set(xlim=(0,300),xlabel="Candidate sets by pairwise inversion count")
    ax.legend([Rectangle((0,0),1,1,color=c) for c in (LIGHT,"#B5D9ED",BLUE,"#00496F")],["0","1-5","6-10","11-15"],frameon=False,ncol=4,fontsize=7,loc="upper center",bbox_to_anchor=(.5,-.22))
    title(ax,"C  Credibility does change the ranking")
    ax=fig.add_subplot(gs[1,1]); ax.axis("off")
    for i,(k,label) in enumerate(zip(METHODS,LABELS)):
        ax.text(0,.96-i*.105,f"{i+1}  {label}",fontsize=8)
    ax.text(0,-.04,"591 common records; ranking cost is additional.\nIndices identify panel A; no test of superiority.",fontsize=7.2,color=GRAY)
    save(fig,"fig06_mitigation")


def diagnostics():
    fig=plt.figure(figsize=(7.25,5.35),layout="constrained")
    gs=fig.add_gridspec(2,2,height_ratios=[1.05,1])
    ax=fig.add_subplot(gs[0,:]); patterns=["".join(x) for x in itertools.product("01",repeat=4)]
    mat=np.array([[R["controlled"]["strata"][s]["signatures"].get(k,0) for k in patterns] for s in STRATA])
    shares=mat/np.array([515,637])[:,None]*100
    ax.imshow(shares,cmap="Blues",vmin=0,vmax=85,aspect="auto")
    for (i,j),n in np.ndenumerate(mat): ax.text(j,i,str(n),ha="center",va="center",fontsize=8,color="white" if shares[i,j]>45 else "#222222")
    ax.set_xticks(range(16),patterns,rotation=60,ha="right"); ax.set_yticks([0,1],["Stable (515)","Rescuable (637)"]); ax.tick_params(length=0)
    ax.set_xlabel("Signature: top-SF, top-FS, bottom-SF, bottom-FS; 1 = scored correct")
    title(ax,"A  Four-condition signatures separate fragility from persistent failure")
    ax=fig.add_subplot(gs[1,0])
    for i,s in enumerate(STRATA):
        row=R["controlled"]["strata"][s]; left=0
        for key,color in (("all_correct",BLUE),("mixed",GREEN),("all_wrong",ORANGE)):
            value=100*row[key]/row["n"]; ax.barh(i,value,left=left,color=color,height=.55)
            if value>5: ax.text(left+value/2,i,f"{value:.1f}%",ha="center",va="center",color="white",fontsize=8)
            left+=value
    ax.set_yticks([0,1],["Stable","Rescuable"]); ax.invert_yaxis(); ax.set(xlim=(0,100),xlabel="Records (%)")
    ax.legend(["All correct","Mixed","All wrong"],frameon=False,ncol=1,loc="upper center",bbox_to_anchor=(.5,-.22),fontsize=7.5)
    title(ax,"B  Persistence after adding conflict")
    ax=fig.add_subplot(gs[1,1])
    for i,k in enumerate(("permutation","repeated")):
        row=R["controlled"]["voting"][k]; left=0
        for key,color in (("correct",BLUE),("wrong_plurality",ORANGE),("tie_or_empty",LIGHT)):
            n=row["counts"].get(key,0); ax.barh(i,n,left=left,color=color,height=.55)
            if n>20: ax.text(left+n/2,i,str(n),ha="center",va="center",color="white" if key!="tie_or_empty" else "#222222",fontsize=8)
            left+=n
    ax.set_yticks([0,1],["Four orders","Four repeats"]); ax.invert_yaxis(); ax.set(xlim=(0,558),xlabel="Records (N = 558)")
    ax.legend(["Correct","Wrong plurality","Tie / empty"],frameon=False,fontsize=7.5,loc="upper center",bbox_to_anchor=(.5,-.22))
    title(ax,"C  Aggregation outcomes")
    save(fig,"fig07_diagnostics")


def graphical():
    fig,axs=plt.subplots(1,3,figsize=(7.25,2.9),layout="constrained")
    fig.suptitle("Evidence order and answer correction",fontweight="bold",fontsize=13)
    axs[0].bar([0,1],[2.7184466,12.244898],color=[BLUE,GREEN],width=.58)
    axs[0].set(xticks=[0,1],xticklabels=["Stable", "Rescuable"],ylabel="Support-first advantage (pp)",ylim=(0,16))
    for i,v in enumerate((2.7,12.2)): axs[0].text(i,v+.5,str(v),ha="center",fontsize=9)
    title(axs[0],"Controlled effect")
    axs[1].barh(0,370,color=ORANGE,height=.5); axs[1].barh(0,41,left=370,color=BLUE,height=.5); axs[1].barh(0,3,left=411,color=GREEN,height=.5)
    axs[1].text(185,0,"370",ha="center",va="center",color="white",fontsize=11)
    axs[1].set(yticks=[],xlim=(0,414),ylim=(-.8,.8),xlabel="414 changing InfoSeek records")
    axs[1].text(0,.48,"370 remain wrong in every order",fontsize=8)
    axs[1].text(0,-.48,"41 change correctness; 3 stay correct",fontsize=7)
    title(axs[1],"Instability is not correction")
    axs[2].plot([0,1],[59.2217,58.5448],color=GRAY,lw=1.2)
    axs[2].scatter([0,1],[59.2217,58.5448],color=[BLUE,ORANGE],s=40,zorder=3)
    axs[2].set(xticks=[0,1],xticklabels=["Original","Credibility"],ylim=(58,60),ylabel="Common-set accuracy (%)")
    axs[2].text(.5,59.7,"293/300 lists reordered",ha="center",fontsize=8)
    axs[2].text(.5,58.12,"No reliable improvement; N = 591",ha="center",fontsize=7)
    title(axs[2],"Activity is not utility")
    save(fig,"graphical_abstract")


def main():
    for fn in (design,controlled,robustness,natural,conflicts,mitigation,diagnostics,graphical): fn()
    print("Generated 7 main composite figures and one graphical abstract; no main-text forest plots.")


if __name__=="__main__": main()
