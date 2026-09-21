"""Generate vector publication figures and LaTeX tables from paper_results.json."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "analysis/paper_results.json").read_text(encoding="utf-8"))
FIG = ROOT / "figures"
TABLE = ROOT / "tables"
FIG.mkdir(exist_ok=True)
TABLE.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 11,
                     "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300})
BLUE = "#0072B2"
RED = "#D55E00"
GREEN = "#009E73"
GRAY = "#666666"
MODELS = ["Qwen/Qwen3-VL-8B-Instruct", "Qwen/Qwen3.5-9B", "Pro/moonshotai/Kimi-K2.6", "zai-org/GLM-4.5V", "gemini-3.8-flash"]
LABELS = dict(zip(MODELS, ["Qwen3-VL-8B", "Qwen3.5-9B", "Kimi-K2.6", "GLM-4.5V", "Gemini 3.8"]))
MLABEL = {"original": "Original", "random": "Random", "reverse": "Reverse", "cross_encoder": "Cross-encoder", "llm_reranker": "LLM reranker", "permutation_vote": "Permutation vote", "budget_matched_self_consistency": "Repeated original (2)", "credibility": "Credibility"}
MECH = {"original": "Original wording", "paraphrase_1": "Paraphrase 1", "paraphrase_2": "Paraphrase 2", "length_matched": "Word-count matched", "distractor_0": "0 distractors", "distractor_2": "2 distractors", "distractor_4": "4 distractors"}


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight", pad_inches=.06)
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight", pad_inches=.06)
    plt.close(fig)


def point(ax, value, y, color=BLUE, marker="o", label=None):
    x = 100 * value["difference"]
    lo, hi = np.array(value["ci95"]) * 100
    ax.errorbar(x, y, xerr=[[max(0, x-lo)], [max(0, hi-x)]], fmt=marker, color=color, capsize=2.5, ms=4.5, lw=1.2, label=label)


def forest_axis(ax, labels, xlabel, xlim=None):
    ax.axvline(0, color="#999999", lw=.7, zorder=0)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=.15)
    if xlim:
        ax.set_xlim(xlim)


def design():
    fig = plt.figure(figsize=(7.15, 4.35))
    ax = fig.add_axes([.01,.02,.98,.96]); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis("off")
    ax.text(0,97,"A  Independent screening",weight="bold",fontsize=11)
    ax.text(1,87,"400 questions  |  4 tasks  |  5 model endpoints",fontsize=9)
    ax.text(1,78,"Three no-evidence calls per question and model",fontsize=9)
    for x, title, detail, color in [(1,"Stable-correct","3/3 correct\n515 complete records",BLUE),(36,"Support-rescuable","0/3 correct; support-only correct\n637 complete records",GREEN),(73,"Other outcomes","Excluded from\nconfirmatory strata",GRAY)]:
        ax.plot([x,x+25],[72,72],color=color,lw=2)
        ax.text(x,67,title,color=color,weight="bold",fontsize=9)
        ax.text(x,60,detail,va="top",fontsize=8,linespacing=1.5)
    ax.text(0,41,"B  Same evidence; support and foil exchange positions",weight="bold",fontsize=10)
    colors={"S":"#CDECE2","F":"#F6DBC8","N":"#ECECEC"}
    orders=[("Top / SF",["S","F","N","N","N"]), ("Top / FS",["F","S","N","N","N"]), ("Bottom / SF",["N","N","N","S","F"]), ("Bottom / FS",["N","N","N","F","S"])]
    for j,(label,order) in enumerate(orders):
        x = 0 if j<2 else 51; y = 26 if j%2==0 else 14
        ax.text(x,y+3,label,fontsize=8,va="center")
        for k,role in enumerate(order):
            bx=x+18+k*5.5
            ax.add_patch(Rectangle((bx,y),4.7,7,facecolor=colors[role],edgecolor="#999999",lw=.5))
            ax.text(bx+2.35,y+3.5,role,ha="center",va="center",fontsize=8)
    ax.text(0,1,"S: answer-bearing support    F: scorer-defined foil    N: neutral filler",fontsize=8,color=GRAY)
    save(fig,"fig01_design")


def controlled():
    fig,axs=plt.subplots(1,2,figsize=(7.15,3.45),gridspec_kw={"width_ratios":[1.35,1]},layout="constrained")
    for i,m in enumerate(MODELS):
        v=D["controlled"]["by_model"][m]
        point(axs[0],v["stable_correct"],i-.12,BLUE,"o","Stable-correct" if i==0 else None)
        point(axs[0],v["support_rescuable"],i+.12,RED,"s","Support-rescuable" if i==0 else None)
        point(axs[1],v["interaction"],i,GREEN)
    forest_axis(axs[0],[LABELS[m] for m in MODELS],"Support-first minus foil-first (pp)",(-10,44))
    forest_axis(axs[1],[""]*5,"Difference between strata (pp)",(-12,31))
    axs[0].set_title("A  Order effect by stratum",loc="left")
    axs[1].set_title("B  Dependency interaction",loc="left")
    axs[0].legend(frameon=False,fontsize=8,loc="lower right")
    save(fig,"fig02_controlled")


def robustness():
    fig,axs=plt.subplots(1,2,figsize=(7.15,3.7),gridspec_kw={"width_ratios":[1.05,1.25]},layout="constrained")
    for i,key in enumerate(MECH):
        point(axs[0],D["mechanism"]["pooled"][key],i)
    forest_axis(axs[0],list(MECH.values()),"Support-first minus foil-first (pp)",(-1,25))
    axs[0].set_title("A  Pooled robustness",loc="left")
    mat=np.array([[D["mechanism"]["by_model"][m][k]["difference"]*100 for m in MODELS[:4]] for k in MECH])
    im=axs[1].imshow(mat,vmin=-50,vmax=50,cmap="RdBu_r",aspect="auto")
    axs[1].set_yticks(range(7),[""]*7)
    axs[1].set_xticks(range(4),["Qwen3-VL","Qwen3.5","Kimi","GLM"],rotation=30,ha="right")
    for (i,j),v in np.ndenumerate(mat):
        axs[1].text(j,i,f"{v:+.1f}",ha="center",va="center",fontsize=8,color="white" if abs(v)>30 else "#222222")
    axs[1].set_title("B  Model-specific effects (pp)",loc="left")
    fig.colorbar(im,ax=axs[1],shrink=.7,pad=.03)
    save(fig,"fig03_robustness")


def natural():
    fig,axs=plt.subplots(1,3,figsize=(7.15,4.4),sharey=True,layout="constrained")
    for j,ds in enumerate(("BoolQ","InfoSeek","StrategyQA")):
        root="kbs_natural_boolq_v1" if ds=="BoolQ" else "kbs_natural_v1"
        for i,m in enumerate(MODELS):
            v=D["natural"][root]["cells"][m][ds]["all"]
            point(axs[j],v["original"]["net_correction"],i,BLUE)
            axs[j].text(-13,i+.26,f"{100*v['permutation_sensitive_rate']:.1f}% changed",fontsize=6.8,color=GRAY)
        forest_axis(axs[j],[LABELS[m] for m in MODELS] if j==0 else [""]*5,"Net correction (pp)",(-15,29))
        axs[j].set_title(ds,loc="left")
        axs[j].set_ylim(4.7,-.6)
    axs[0].set_yticks(range(5),[LABELS[m] for m in MODELS])
    save(fig,"fig04_natural")


def conflicts():
    fig,axs=plt.subplots(1,2,figsize=(7.15,2.65),gridspec_kw={"width_ratios":[1.1,1]},layout="constrained")
    ds=["InfoSeek","BoolQ","StrategyQA"]
    for i,k in enumerate(ds):
        v=D["natural"]["pairs_by_dataset"][k]
        if v["questions"]>1:
            point(axs[0],v,i)
        else:
            axs[0].scatter([0],[i],marker="x",color=GRAY,s=30)
            axs[0].text(1,i,"CI not informative",va="center",fontsize=7,color=GRAY)
    forest_axis(axs[0],[f"{k} (q={D['natural']['pairs_by_dataset'][k]['questions']})" for k in ds],"Support-first minus foil-first (pp)",(-6,17))
    axs[0].set_title("A  Natural conflict pairs",loc="left")
    for i,k in enumerate(ds): point(axs[1],D["natural"]["by_dataset"][k]["delta"],i,RED)
    forest_axis(axs[1],ds,"Original minus reverse (pp)",(-4,4))
    axs[1].set_title("B  Unselected retrieval order",loc="left")
    save(fig,"fig05_conflicts")


def mitigation():
    fig,axs=plt.subplots(1,2,figsize=(7.15,4.15),gridspec_kw={"width_ratios":[1.5,1]},layout="constrained")
    order=["original","random","reverse","cross_encoder","llm_reranker","permutation_vote","budget_matched_self_consistency","credibility"]
    for i,k in enumerate(order): point(axs[0],D["reranking"]["methods"][k]["net_correction"],i,RED if k=="credibility" else BLUE)
    forest_axis(axs[0],[MLABEL[k] for k in order],"Net correction (pp)",(-1,11))
    axs[0].set_title("A  Natural reranking experiment",loc="left")
    cost=D["reranking"]["ranking"]
    vals=[cost["llm_reranker_tokens"]/1e6,cost["credibility_tokens"]/1e6]
    axs[1].bar([0,1],vals,color=[BLUE,RED],width=.58)
    axs[1].set_xticks([0,1],["LLM\nreranker","Credibility"])
    axs[1].set_ylim(0,1.4)
    axs[1].set_ylabel("Ranking tokens (millions)")
    for i,v in enumerate(vals): axs[1].text(i,v+.025,f"{v:.3f}",ha="center",fontsize=9)
    axs[1].text(.5,1.3,"300 shared candidate sets",ha="center",fontsize=8,color=GRAY)
    axs[1].set_title("B  Additional ranking cost",loc="left")
    save(fig,"fig06_mitigation")


def sensitivity():
    fig,axs=plt.subplots(1,2,figsize=(7.15,3.3),layout="constrained")
    for i,m in enumerate(MODELS): point(axs[0],D["controlled"]["leave_one_model_out"][m]["interaction"],i,GREEN)
    forest_axis(axs[0],["Without "+LABELS[m] for m in MODELS],"Dependency interaction (pp)",(0,19))
    axs[0].set_title("A  Leave-one-model-out",loc="left")
    vals=D["controlled_mitigation"]
    for i,k in enumerate(("single","vote","sc")): point(axs[1],vals[k],i,RED if k=="vote" else BLUE)
    forest_axis(axs[1],["Single top-SF","Four orders","Four repeated top-SF"],"Accuracy (%)",(15,52))
    axs[1].set_title("B  Controlled voting",loc="left")
    save(fig,"fig07_sensitivity")


def graphical():
    fig,ax=plt.subplots(figsize=(7.5,2.75),layout="constrained"); ax.axis("off"); ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.text(.01,.94,"Evidence order and correction",fontsize=16,weight="bold")
    ax.text(.01,.74,"Same support + foil\nDifferent relative order",fontsize=11,linespacing=1.5)
    ax.add_patch(FancyArrowPatch((.31,.60),(.41,.60),arrowstyle="->",mutation_scale=15,lw=1.2))
    ax.text(.44,.76,"12.2 pp",fontsize=23,color=RED,weight="bold")
    ax.text(.44,.57,"Support-rescuable\norder effect",fontsize=10,linespacing=1.4)
    ax.text(.77,.76,"2.7 pp",fontsize=23,color=BLUE,weight="bold")
    ax.text(.77,.57,"Stable-correct\norder effect",fontsize=10,linespacing=1.4)
    ax.plot([.01,.98],[.29,.29],color="#BBBBBB",lw=.7)
    ax.text(.01,.18,"5 endpoints / 4 controlled tasks",fontsize=10)
    ax.text(.01,.05,"386 independent questions",fontsize=10,color=GRAY)
    ax.text(.52,.18,"Natural effects are task-dependent",fontsize=10)
    ax.text(.52,.05,"Credibility ranking fails its success criterion",fontsize=9,color=GRAY)
    save(fig,"graphical_abstract")


def effect(v):
    return f"{v['difference']:+.3f} [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}]"


def table(name, header, rows, cols):
    text="\\begin{tabular}{"+cols+"}\n\\toprule\n"+" & ".join(header)+r" \\"+"\n\\midrule\n"
    text+="\n".join(" & ".join(map(str,row))+r" \\" for row in rows)+"\n\\bottomrule\n\\end{tabular}\n"
    (TABLE/f"{name}.tex").write_text(text,encoding="utf-8")


def tables():
    c=D["controlled"]
    rows=[]
    for m in MODELS:
        v=c["by_model"][m]
        rows.append([LABELS[m],v["stable_correct"]["n"],effect(v["stable_correct"]),v["support_rescuable"]["n"],effect(v["support_rescuable"]),effect(v["interaction"])])
    v=c["primary"]
    rows.append(["Pooled",515,effect(v["stable_correct"]),637,effect(v["support_rescuable"]),effect(v["interaction"])])
    table("controlled",["Model","$N_C$","$\\Delta_C$ [95\\% CI]","$N_R$","$\\Delta_R$ [95\\% CI]","$\\Gamma$ [95\\% CI]"],rows,"lrlrll")
    rows=[]
    for ds,v in c["by_dataset"].items(): rows.append([ds,v["stable_correct"]["n"],v["support_rescuable"]["n"],effect(v["support_rescuable"]),effect(v["interaction"])])
    table("datasets",["Dataset","$N_C$","$N_R$","$\\Delta_R$ [95\\% CI]","$\\Gamma$ [95\\% CI]"],rows,"lrrll")
    rows=[]
    for ds in ("BoolQ","InfoSeek","StrategyQA"):
        root="kbs_natural_boolq_v1" if ds=="BoolQ" else "kbs_natural_v1"
        for m in MODELS:
            v=D["natural"][root]["cells"][m][ds]["all"]
            rows.append([ds,LABELS[m],v["n"],f"{v['accuracy']['baseline']:.3f}",f"{v['accuracy']['original']:.3f}",effect(v["original"]["net_correction"]),f"{v['permutation_sensitive_rate']:.3f}"])
    table("natural_full",["Task","Model","$N$","Base","Orig.","Net [95\\% CI]","Changed"],rows,"llrrrlr")
    rows=[]
    for k in ["original","random","reverse","cross_encoder","llm_reranker","permutation_vote","budget_matched_self_consistency","credibility"]:
        v=D["reranking"]["methods"][k]
        rows.append([MLABEL[k],v["n"],f"{v['accuracy']:.3f}",effect(v["net_correction"]),f"{v['ece']:.3f}",f"{v['brier']:.3f}",f"{v['answer_calls']:,}"])
    table("reranking",["Method","$N$","Acc.","Net [95\\% CI]","ECE","Brier","Calls"],rows,"lrrlrrr")
    table("mechanism",["Condition","$N$","Questions","Order effect [95\\% CI]"],[[MECH[k],v["n"],v["questions"],effect(v)] for k,v in D["mechanism"]["pooled"].items()],"lrrl")
    table("paired_controls",["Control","Paired $N$","Credibility minus control [95\\% CI]"],[[MLABEL[k],v["n"],effect(v)] for k,v in D["reranking"]["paired_against_all_controls"].items()],"lrl")
    table("secondary_tests",["Grouping","Model or task","Raw $p$","Holm-adjusted $p$"],[[r["kind"],LABELS.get(r["group"],r["group"]),f"{r['p']:.4f}",f"{r['holm_p']:.4f}"] for r in c["secondary_cluster_signflip"]],"llrr")
    table("common_complete",["Method","Common-set accuracy"],[[MLABEL[k],f"{v:.3f}"] for k,v in D["reranking"]["common_complete_accuracy"].items()],"lr")
    macros={"PrimaryStable":effect(c["primary"]["stable_correct"]),"PrimaryRescuable":effect(c["primary"]["support_rescuable"]),"PrimaryInteraction":effect(c["primary"]["interaction"]),"NaturalInitial":effect(D["natural"]["initial_pairs"]),"NaturalBoolQ":effect(D["natural"]["pairs_by_dataset"]["BoolQ"]),"VoteDifference":effect(D["controlled_mitigation"]["delta"]),"LexicalInteraction":effect(c["lexical_containment_sensitivity"]["primary"]["interaction"]),"LexicalExcluded":str(c["lexical_containment_sensitivity"]["excluded_complete_records"])}
    macros.update({"VoteAccuracy": effect(D["controlled_mitigation"]["vote"]), "RepeatAccuracy": effect(D["controlled_mitigation"]["sc"])})
    (TABLE/"numbers.tex").write_text("\n".join("\\newcommand{\\"+k+"}{"+v+"}" for k,v in macros.items())+"\n",encoding="utf-8")
    table("leave_one_out", ["Excluded endpoint", "Interaction [95\\% CI]"], [[LABELS[m], effect(v["interaction"])] for m, v in c["leave_one_model_out"].items()], "ll")
    table("natural_pooled", ["Task", "Net correction [95\\% CI]", "Original - reverse [95\\% CI]"], [[ds, effect(v["net"]), effect(v["delta"])] for ds, v in D["natural"]["by_dataset"].items()], "lll")
    table("natural_conflicts", ["Task", "Questions", "Records", "SF - FS [95\\% CI]"], [[ds, v["questions"], v["n"], effect(v) if v["questions"] > 1 else "Not informative"] for ds, v in D["natural"]["pairs_by_dataset"].items()], "lrrl")
    revision = json.loads((ROOT / "analysis/revision_diagnostics.json").read_text(encoding="utf-8"))
    rows = []
    for task, v in revision["natural"]["tasks"].items():
        categories, counts = v["categories"], v["transition"]["counts"]
        rows.append([task, v["n"], counts["01"], counts["10"], v["n"] - categories["invariant"], categories["correctness_changes"], f"{100*v['original_accuracy']:.1f}", f"{100*v['observed_best']:.1f}"])
    table("revision_accounting", ["Task", "$N$", "Repair", "Damage", "Changed strings", "Changed correctness", "Original (\\%)", "Best saved order (\\%)"], rows, "lrrrrrrr")
    rows = []
    for key, label in (("original", "Original"), ("cross_encoder", "Cross-encoder"), ("llm_reranker", "LLM relevance"), ("credibility", "Credibility"), ("permutation_vote", "Four-order vote"), ("budget_matched_self_consistency", "Repeated original (2)")):
        v = revision["ranking"]["common_complete"][key]
        counts = v["vs_original"]["counts"]
        rows.append([label, f"{100*v['accuracy']:.2f}", counts["01"], counts["10"], f"{v['answer_calls']:,}", f"{v['answer_tokens']:,}"])
    table("revision_activity", ["Method", "Accuracy (\\%)", "Repairs", "Damage", "Answer calls", "Answer tokens"], rows, "lrrrrr")
    coverage = json.loads((ROOT / "analysis/model_coverage.json").read_text(encoding="utf-8"))
    rows = []
    for model, methods in coverage["ranking_common_by_reader"].items():
        for method, v in methods.items():
            rows.append([LABELS[model], MLABEL[method], v["n"], f"{100*v['accuracy']:.2f}", v["repairs"], v["damage"], effect(v["vs_original"])])
    table("reader_ranking", ["Reader", "Method", "$N$", "Accuracy (\\%)", "Repairs", "Damage", "Change from original [95\\% CI]"], rows, "llrrrrl")


if __name__=="__main__":
    tables()
    from make_journal_figures import main
    main()
    from make_followup_figures import main as followup_main
    followup_main()
