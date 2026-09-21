"""Paper-only, question-clustered reanalysis of immutable experiment records."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

PAPER = Path(__file__).resolve().parents[1]
PROJECT = PAPER.parent
sys.path.insert(0, str(PROJECT))
from dgms.metrics import normalize
from dgms.analyze_order_confirmatory import _majority_answer
from dgms.order_confirmatory import answer_correct
from scripts.analyze_kbs_mechanism import PAIRS, result as mechanism_result
from scripts.analyze_kbs_credibility import flatten, METHODS, cluster_bootstrap

OUT = PAPER / "analysis"
SEED = 20260918
ITERATIONS = 10000
INPUTS = {}


def read(path):
    p = PROJECT / path
    INPUTS[str(p.relative_to(PROJECT)).replace("\\", "/")] = hashlib.sha256(p.read_bytes()).hexdigest()
    return json.loads(p.read_text(encoding="utf-8"))


def records(folder):
    return [read(p.relative_to(PROJECT)) for p in sorted((PROJECT / folder).glob("*.json"))]


def bootstrap(rows, fields=("delta",)):
    ids = sorted({r["qid"] for r in rows})
    lookup = {v: i for i, v in enumerate(ids)}
    sums = np.zeros((len(ids), len(fields)))
    counts = np.zeros_like(sums)
    for r in rows:
        i = lookup[r["qid"]]
        for j, key in enumerate(fields):
            if key in r:
                sums[i, j] += r[key]
                counts[i, j] += 1
    point = sums.sum(axis=0) / counts.sum(axis=0)
    rng = np.random.default_rng(SEED)
    chosen = rng.integers(len(ids), size=(ITERATIONS, len(ids)))
    draws = sums[chosen].sum(axis=1) / counts[chosen].sum(axis=1)
    answer = {key: {"difference": float(point[j]), "ci95": np.quantile(draws[:, j], [.025, .975]).tolist(),
                    "n": int(counts[:, j].sum()), "questions": int((counts[:, j] > 0).sum())}
              for j, key in enumerate(fields)}
    if len(fields) == 2:
        d = draws[:, 1] - draws[:, 0]
        answer["interaction"] = {"difference": float(point[1] - point[0]), "ci95": np.quantile(d, [.025, .975]).tolist(), "questions": len(ids)}
    return answer


def cluster_p(rows):
    # Two-sided wild sign-flip test on question-level sums under a symmetric null.
    sums = defaultdict(float)
    for r in rows:
        sums[r["qid"]] += r["delta"]
    a = np.asarray([sums[k] for k in sorted(sums)])
    observed = abs(a.sum())
    rng = np.random.default_rng(SEED)
    null = (rng.choice([-1, 1], size=(ITERATIONS, len(a))) * a).sum(axis=1)
    return float((1 + np.count_nonzero(abs(null) >= observed - 1e-12)) / (ITERATIONS + 1))


def holm(rows):
    largest = 0
    for i, row in enumerate(sorted(rows, key=lambda v: v["p"])):
        largest = max(largest, min(1., row["p"] * (len(rows) - i)))
        row["holm_p"] = largest
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    names = ("top_sf", "top_fs", "bottom_sf", "bottom_fs")
    raw = records("results/order_confirmatory_v1/records") + records("results/kbs_gemini38_v1/order_records")
    rows = []
    for r in raw:
        v = r["variants"]
        if not all(v.get(n, {}).get("ok") for n in names):
            continue
        d = ((v["top_sf"]["correct"] - v["top_fs"]["correct"]) + (v["bottom_sf"]["correct"] - v["bottom_fs"]["correct"])) / 2
        rows.append({"qid": r["sample"]["sample_id"], "entry": r["entry_id"], "model": r["model"], "dataset": r["dataset"], "stratum": r["stratum"], "delta": d, r["stratum"]: d})
    strata = ("stable_correct", "support_rescuable")
    controlled = {"questions": len({r["qid"] for r in rows}), "records": len(rows),
                  "primary": bootstrap(rows, strata)}
    for key in ("model", "dataset"):
        controlled["by_" + key] = {v: bootstrap([r for r in rows if r[key] == v], strata) for v in sorted({r[key] for r in rows})}
    controlled["leave_one_model_out"] = {m: bootstrap([r for r in rows if r["model"] != m], strata) for m in controlled["by_model"]}
    tests = []
    for kind in ("model", "dataset"):
        for group in controlled["by_" + kind]:
            chosen = [r for r in rows if r[kind] == group and r["stratum"] == "support_rescuable"]
            tests.append({"kind": kind, "group": group, "p": cluster_p(chosen)})
    controlled["secondary_cluster_signflip"] = holm(tests)
    plans = read("data/order_confirmatory_v1.json")["samples"] + read("data/kbs_gemini38_confirmatory_v1.json")["samples"]
    overlap_ids = set()
    overlap_records = []
    for e in plans:
        a, b = (" ".join(re.findall(r"\w+", str(e[k]).casefold())) for k in ("support_answer", "foil_answer"))
        if a and b and (f" {a} " in f" {b} " or f" {b} " in f" {a} "):
            overlap_ids.add(e["entry_id"])
            overlap_records.append({"entry": e["entry_id"], "sample": e["sample"]["sample_id"], "support": e["support_answer"], "foil": e["foil_answer"]})
    filtered = [r for r in rows if r["entry"] not in overlap_ids]
    controlled["lexical_containment_sensitivity"] = {"rule": "Exclude entries with whole normalized support string contained in foil or vice versa; no semantic adjudication.", "excluded_complete_records": len(rows) - len(filtered), "primary": bootstrap(filtered, strata), "flagged_entries": overlap_records}
    controlled["legacy_primary"] = read("results/kbs_statistics_v1/summary.json")["primary"]
    controlled["gee"] = read("results/kbs_statistics_v1/summary.json")["gee"]

    natural = {}
    natural_all = []
    pair_all = []
    for root in ("kbs_natural_v1", "kbs_natural_boolq_v1"):
        rs = records(f"results/{root}/answer_records")
        summary = read(f"results/{root}/analysis/summary.json")
        for r in rs:
            cond = r["conditions"]
            base = {"qid": r["sample"]["sample_id"], "model": r["model"], "dataset": r["sample"]["dataset"]}
            if r["sample"].get("cohort") == "complete" and all(cond.get(n, {}).get("ok") for n in ("baseline", "original", "reverse", "shuffle_1", "shuffle_2")):
                natural_all.append({**base, "delta": cond["original"]["correct"] - cond["reverse"]["correct"], "net": cond["original"]["correct"] - cond["baseline"]["correct"], "baseline": cond["baseline"]["correct"], "original": cond["original"]["correct"], "sensitive": int(len({normalize(cond[n]["prediction"]["answer"]) for n in ("original", "reverse", "shuffle_1", "shuffle_2")}) > 1)})
            if all(cond.get(n, {}).get("ok") for n in ("natural_support_first", "natural_foil_first")):
                pair_all.append({**base, "delta": cond["natural_support_first"]["correct"] - cond["natural_foil_first"]["correct"]})
        natural[root] = {"scope": summary["scope"], "retrieval": summary["retrieval"], "scan_pool": summary["scan_pool"], "cells": summary["cells"], "completion": summary["completion"]}
    natural["pairs_by_dataset"] = {ds: bootstrap([r for r in pair_all if r["dataset"] == ds])["delta"] for ds in sorted({r["dataset"] for r in pair_all})}
    natural["initial_pairs"] = bootstrap([r for r in pair_all if r["dataset"] != "BoolQ"])["delta"]
    natural["all_pairs_exploratory"] = bootstrap(pair_all)["delta"]
    natural["overall"] = bootstrap(natural_all, ("delta", "net", "baseline", "original", "sensitive"))
    natural["by_dataset"] = {ds: bootstrap([r for r in natural_all if r["dataset"] == ds], ("delta", "net", "baseline", "original", "sensitive")) for ds in sorted({r["dataset"] for r in natural_all})}

    mechanism_rows = []
    for r in records("results/kbs_mechanism_v1/records"):
        row = {"qid": r["sample"]["sample_id"], "model": r["model"]}
        for label, (sf, fs) in PAIRS.items():
            left, right = mechanism_result(r, sf), mechanism_result(r, fs)
            if left.get("ok") and right.get("ok"):
                row[label] = left["correct"] - right["correct"]
        mechanism_rows.append(row)
    mechanism = {"pooled": bootstrap(mechanism_rows, tuple(PAIRS)),
                 "by_model": {m: bootstrap([r for r in mechanism_rows if r["model"] == m], tuple(PAIRS)) for m in sorted({r["model"] for r in mechanism_rows})}}

    mitigation_rows = []
    for r in raw:
        reps = r.get("canonical_repeats", [])
        if r["stratum"] != "support_rescuable" or len(reps) != 3 or not all(v.get("ok") for v in reps):
            continue
        v = r["variants"]
        perm, _ = _majority_answer([v[n]["prediction"]["answer"] for n in names])
        sc, _ = _majority_answer([v["top_sf"]["prediction"]["answer"]] + [v["prediction"]["answer"] for v in reps])
        alias = r["sample"]["answer_eval"]
        mitigation_rows.append({"qid": r["sample"]["sample_id"], "model": r["model"], "single": v["top_sf"]["correct"], "vote": int(answer_correct(perm, alias)), "sc": int(answer_correct(sc, alias)), "delta": int(answer_correct(perm, alias)) - int(answer_correct(sc, alias))})
    mitigation = bootstrap(mitigation_rows, ("single", "vote", "sc", "delta"))

    fraw = records("results/kbs_credibility_v1/answer_records")
    frows = flatten(fraw)
    fs = read("results/kbs_credibility_v1/analysis/summary.json")
    lookup = {(r["sample_id"], r["model"], r["method"]): r for r in frows}
    paired = {}
    for method in METHODS:
        if method == "credibility":
            continue
        pairs = [{**r, "control": lookup[(r["sample_id"], r["model"], method)]["correct"]} for r in frows if r["method"] == "credibility" and (r["sample_id"], r["model"], method) in lookup]
        paired[method] = {**cluster_bootstrap(pairs, "correct", "control"), "n": len(pairs)}
    keys = {(r["sample_id"], r["model"]) for r in frows}
    complete_keys = {k for k in keys if all((*k, m) in lookup for m in METHODS)}
    fs["paired_against_all_controls"] = paired
    fs["common_complete_records"] = len(complete_keys)
    fs["common_complete_accuracy"] = {m: float(np.mean([lookup[(*k, m)]["correct"] for k in complete_keys])) for m in METHODS}
    report = {"protocol": {"iterations": ITERATIONS, "seed": SEED, "unit": "question", "status": "post-experiment correction; input records unchanged"}, "controlled": controlled, "natural": natural, "mechanism": mechanism, "controlled_mitigation": mitigation, "reranking": fs}
    (OUT / "paper_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "input_hashes.json").write_text(json.dumps(INPUTS, indent=2), encoding="utf-8")
    print(json.dumps({"primary": controlled["primary"], "lexical_sensitivity": {k:v for k,v in controlled["lexical_containment_sensitivity"].items() if k != "flagged_entries"}, "natural_pairs": natural["pairs_by_dataset"], "initial_pairs": natural["initial_pairs"], "mechanism": mechanism["pooled"], "mitigation": mitigation, "f_common": fs["common_complete_records"]}, indent=2))


if __name__ == "__main__":
    main()
