"""Descriptive revision diagnostics from saved records; never calls a model."""
from __future__ import annotations

import itertools
import json
from collections import Counter
from pathlib import Path

import numpy as np

from build_evidence import INPUTS, read, records, normalize, answer_correct, _majority_answer, bootstrap
from scripts.analyze_kbs_credibility import flatten, METHODS

ROOT = Path(__file__).resolve().parents[1]
ORDERS = ("top_sf", "top_fs", "bottom_sf", "bottom_fs")
NATURAL = ("original", "reverse", "shuffle_1", "shuffle_2")


def mean(xs):
    return float(np.mean(xs)) if xs else None


def transition(pairs):
    c = Counter(f"{a}{b}" for a, b in pairs)
    n = len(pairs)
    return {"n": n, "counts": {s: c[s] for s in ("00", "01", "10", "11")},
            "net": (c["01"] - c["10"]) / n if n else None,
            "gross": (c["01"] + c["10"]) / n if n else None}


def controlled_summary(rows):
    signatures = Counter("".join(str(r["variants"][k]["correct"]) for k in ORDERS) for r in rows)
    pairs = [(r["variants"][f"{p}_fs"]["correct"], r["variants"][f"{p}_sf"]["correct"]) for r in rows for p in ("top", "bottom")]
    t = transition(pairs)
    return {"n": len(rows), "questions": len({r["sample"]["sample_id"] for r in rows}), "signatures": dict(signatures),
            "accuracy": {k: mean([r["variants"][k]["correct"] for r in rows]) for k in ORDERS},
            "swaps": t,
            "top_effect": mean([r["variants"]["top_sf"]["correct"] - r["variants"]["top_fs"]["correct"] for r in rows]),
            "bottom_effect": mean([r["variants"]["bottom_sf"]["correct"] - r["variants"]["bottom_fs"]["correct"] for r in rows]),
            "mixed": sum(v for k, v in signatures.items() if k not in ("0000", "1111")),
            "all_wrong": signatures["0000"], "all_correct": signatures["1111"]}


def natural_summary(rows):
    t = transition([(r["conditions"]["baseline"]["correct"], r["conditions"]["original"]["correct"]) for r in rows])
    categories = Counter()
    scoring_normalization_conflicts = 0
    for r in rows:
        c = r["conditions"]
        ys = [c[k]["correct"] for k in NATURAL]
        answers = {normalize(c[k]["prediction"]["answer"]) for k in NATURAL}
        scoring_normalization_conflicts += int(len(set(ys)) > 1 and len(answers) == 1)
        key = "correctness_changes" if len(set(ys)) > 1 else ("wrong_strings_change" if not ys[0] else "correct_strings_change") if len(answers) > 1 else "invariant"
        categories[key] += 1
    successes = [sum(r["conditions"][k]["correct"] for k in NATURAL) for r in rows]
    return {"n": len(rows), "questions": len({r["sample"]["sample_id"] for r in rows}), "transition": t,
            "baseline_accuracy": mean([r["conditions"]["baseline"]["correct"] for r in rows]),
            "original_accuracy": mean([r["conditions"]["original"]["correct"] for r in rows]),
            "categories": {k: categories[k] for k in ("invariant", "correctness_changes", "wrong_strings_change", "correct_strings_change")},
            "scoring_normalization_conflicts": scoring_normalization_conflicts,
            "success_count": {str(k): successes.count(k) for k in range(5)},
            "observed_best": mean([int(x > 0) for x in successes]),
            "observed_worst": mean([int(x == 4) for x in successes]),
            "original_reverse": transition([(r["conditions"]["reverse"]["correct"], r["conditions"]["original"]["correct"]) for r in rows])}


def inversions(order):
    ranks = [int(x[1:]) for x in order]
    return sum(a > b for a, b in itertools.combinations(ranks, 2))


def main():
    controlled = records("results/order_confirmatory_v1/records") + records("results/kbs_gemini38_v1/order_records")
    controlled = [r for r in controlled if all(r["variants"].get(k, {}).get("ok") for k in ORDERS)]
    models = sorted({r["model"] for r in controlled})
    datasets = sorted({r["dataset"] for r in controlled})
    strata = ("stable_correct", "support_rescuable")
    cs = {s: controlled_summary([r for r in controlled if r["stratum"] == s]) for s in strata}
    cells = {m: {s: controlled_summary([r for r in controlled if r["model"] == m and r["stratum"] == s]) for s in strata} for m in models}
    task_cells = {m: {d: {s: controlled_summary([r for r in controlled if r["model"] == m and r["dataset"] == d and r["stratum"] == s]) for s in strata} for d in datasets} for m in models}
    plans = read("data/order_confirmatory_v1.json")["samples"] + read("data/kbs_gemini38_confirmatory_v1.json")["samples"]
    lookup = {r["entry_id"]: r for r in plans}
    nonanswers = {"", "unknown", "abstain", "idontknow", "cannotdetermine", "uncertain", "notanswerable"}
    excluded = [r for r in controlled if normalize(lookup[r["entry_id"]]["foil_answer"]) in nonanswers]
    retained = [r for r in controlled if r not in excluded]
    cleaned = [{"qid": r["sample"]["sample_id"], r["stratum"]: sum(r["variants"][f"{p}_sf"]["correct"] - r["variants"][f"{p}_fs"]["correct"] for p in ("top", "bottom")) / 2} for r in retained]
    nonanswer_sensitivity = {"rule": sorted(nonanswers), "excluded": len(excluded), "excluded_by_foil": dict(Counter(normalize(lookup[r["entry_id"]]["foil_answer"]) for r in excluded)), "primary": bootstrap(cleaned, strata)}
    foil_sources = {s: dict(Counter(r["foil_source"] for r in controlled if r["stratum"] == s)) for s in strata}
    overlap = {s: {r["sample"]["sample_id"] for r in controlled if r["stratum"] == s} for s in strata}
    voting = {}
    vr = [r for r in controlled if r["stratum"] == "support_rescuable" and len(r.get("canonical_repeats", [])) == 3 and all(x.get("ok") for x in r["canonical_repeats"])]
    for key in ("permutation", "repeated"):
        outcome = Counter()
        suppressed = 0
        for r in vr:
            calls = [r["variants"][k] for k in ORDERS] if key == "permutation" else [r["variants"]["top_sf"], *r["canonical_repeats"]]
            answer, tie = _majority_answer([c["prediction"]["answer"] for c in calls])
            good = answer_correct(answer, r["sample"]["answer_eval"])
            outcome["correct" if good else "tie_or_empty" if tie else "wrong_plurality"] += 1
            suppressed += int(any(c["correct"] for c in calls) and not good)
        voting[key] = {"n": len(vr), "counts": dict(outcome), "success_available_but_lost": suppressed}
    cases = []
    for signature in ("1010", "0101", "0000", "1111"):
        candidates = [r for r in controlled if r["stratum"] == "support_rescuable" and r["dataset"] in ("BoolQ", "StrategyQA") and normalize(lookup[r["entry_id"]]["foil_answer"]) in ("yes", "no") and "".join(str(r["variants"][k]["correct"]) for k in ORDERS) == signature]
        if not candidates:
            continue
        r = min(candidates, key=lambda r: (len(r["sample"]["question"]), r["entry_id"]))
        p = lookup[r["entry_id"]]
        cases.append({"entry_id": r["entry_id"], "qid": r["sample"]["sample_id"], "question": r["sample"]["question"], "dataset": r["dataset"], "model": r["model"], "support": p["support_answer"], "foil": p["foil_answer"], "foil_source": r["foil_source"], "signature": signature, "answers": {k: r["variants"][k]["prediction"]["answer"] for k in ORDERS}})

    natural, candidates = [], []
    for folder in ("kbs_natural_v1", "kbs_natural_boolq_v1"):
        natural.extend(records(f"results/{folder}/answer_records"))
        candidates.extend(records(f"results/{folder}/candidate_records"))
    nr = [r for r in natural if r["sample"].get("cohort") == "complete" and all(r["conditions"].get(k, {}).get("ok") for k in ("baseline", *NATURAL))]
    tasks = ("BoolQ", "InfoSeek", "StrategyQA")
    ns = {d: natural_summary([r for r in nr if r["sample"]["dataset"] == d]) for d in tasks}
    nc = {d: {m: natural_summary([r for r in nr if r["sample"]["dataset"] == d and r["model"] == m]) for m in models} for d in tasks}
    pairs = {d: transition([(r["conditions"]["natural_foil_first"]["correct"], r["conditions"]["natural_support_first"]["correct"]) for r in natural if r["sample"]["dataset"] == d and all(r["conditions"].get(k, {}).get("ok") for k in ("natural_support_first", "natural_foil_first"))]) for d in tasks}
    coverage = {}
    for d in tasks:
        cr = [r for r in candidates if r["sample"]["dataset"] == d]
        status = Counter()
        for r in cr:
            if not r.get("labels", {}).get("ok"):
                status["invalid_labels"] += 1
                continue
            labs = {x["label"] for x in r["labels"]["items"].values()}
            status["conflict" if {"support", "foil"} <= labs else "support_only" if "support" in labs else "no_support"] += 1
        coverage[d] = {"n": len(cr), "counts": dict(status)}

    ranks = records("results/kbs_credibility_v1/ranking_records")
    rankings = {}
    for method in ("cross_encoder", "llm_reranker", "credibility"):
        distances = [inversions(r["orders"][method]) for r in ranks]
        rankings[method] = {"n": len(ranks), "inversions": distances, "mean_inversions": mean(distances), "unchanged": distances.count(0), "top1_retained": sum(r["orders"][method][0] == "E1" for r in ranks), "fallback": sum(r["fallbacks"][method] for r in ranks)}
    fr = flatten(records("results/kbs_credibility_v1/answer_records"))
    fl = {(r["sample_id"], r["model"], r["method"]): r for r in fr}
    common = sorted({(r["sample_id"], r["model"]) for r in fr if all((r["sample_id"], r["model"], k) in fl for k in METHODS)})
    fs = {}
    for method in METHODS:
        rows = [fl[(*k, method)] for k in common]
        fs[method] = {"n": len(rows), "accuracy": mean([r["correct"] for r in rows]), "answer_calls": sum(r["calls"] for r in rows), "answer_tokens": sum(r["tokens"] for r in rows), "vs_original": transition([(fl[(*k, "original")]["correct"], fl[(*k, method)]["correct"]) for k in common])}
    rank_by_q = {r["sample_id"]: r for r in ranks}
    distance_groups = {}
    for label, lower, upper in (("unchanged", 0, 0), ("1-5 inversions", 1, 5), ("6-15 inversions", 6, 15)):
        keys = [k for k in common if lower <= inversions(rank_by_q[k[0]]["orders"]["credibility"]) <= upper]
        distance_groups[label] = transition([(fl[(*k, "original")]["correct"], fl[(*k, "credibility")]["correct"]) for k in keys])
    result = {"status": "post-experiment descriptive diagnostics; no new model calls or independent replication", "controlled": {"strata": cs, "models": cells, "cells": task_cells, "foil_sources": foil_sources, "nonanswer_sensitivity": nonanswer_sensitivity, "questions_in_both_strata": len(overlap[strata[0]] & overlap[strata[1]]), "voting": voting, "cases": cases}, "natural": {"tasks": ns, "cells": nc, "conflict_pairs": pairs, "candidate_coverage": coverage}, "ranking": {"permutations": rankings, "common_complete": fs, "distance_groups": distance_groups}}
    (ROOT / "analysis/revision_diagnostics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (ROOT / "analysis/revision_input_hashes.json").write_text(json.dumps(INPUTS, indent=2), encoding="utf-8")
    print(json.dumps({"controlled": cs, "foil_sources": foil_sources, "voting": voting, "cases": cases, "natural": ns, "coverage": coverage, "ranking": {k: {x: v for x, v in r.items() if x != "inversions"} for k, r in rankings.items()}, "distance_groups": distance_groups}, indent=2))


if __name__ == "__main__":
    main()
