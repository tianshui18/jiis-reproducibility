"""Audit saved endpoint coverage and expose reader-specific ranking results."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from build_evidence import INPUTS, PROJECT, records
from scripts.analyze_kbs_credibility import flatten, METHODS, cluster_bootstrap

ROOT = Path(__file__).resolve().parents[1]
GEMINI = "gemini-3.8-flash"


def main():
    inventory = defaultdict(Counter)
    for path in sorted((PROJECT / "results").rglob("*.json")):
        if any(part in ("cache", "quarantine_non_utf8") for part in path.parts):
            continue
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict) and isinstance(data.get("model"), str):
            inventory[path.relative_to(PROJECT / "results").parts[0]][data["model"]] += 1
    screen = records("results/kbs_gemini38_v1/screen_records")
    order = records("results/kbs_gemini38_v1/order_records")
    baseline = [v for r in screen for v in r["baselines"]]
    support = [r["support_only"] for r in screen if r.get("support_only")]
    order_calls = [v for r in order for v in r["variants"].values()]
    natural = records("results/kbs_natural_v1/answer_records") + records("results/kbs_natural_boolq_v1/answer_records")
    stages = {}
    names = ("baseline", "original", "reverse", "shuffle_1", "shuffle_2")
    for task in ("BoolQ", "InfoSeek", "StrategyQA"):
        rows = [r for r in natural if r["model"] == GEMINI and r["sample"]["dataset"] == task]
        cohort = [r for r in rows if r["sample"].get("cohort") == "complete"]
        calls = [r["conditions"].get(k, {}) for r in cohort for k in names]
        pairs = [r for r in rows if all(r["conditions"].get(k, {}).get("ok") for k in ("natural_support_first", "natural_foil_first"))]
        stages[task] = {"planned_questions": len(cohort), "complete_records": sum(all(r["conditions"].get(k, {}).get("ok") for k in names) for r in cohort), "successful_main_conditions": sum(bool(v.get("ok")) for v in calls), "planned_main_conditions": len(calls), "complete_conflict_pairs": len(pairs)}
    raw = records("results/kbs_credibility_v1/answer_records")
    flat = flatten(raw)
    lookup = {(r["sample_id"], r["model"], r["method"]): r for r in flat}
    common = sorted({(r["sample_id"], r["model"]) for r in flat if all((r["sample_id"], r["model"], method) in lookup for method in METHODS)})
    readers = {}
    for model in sorted({r["model"] for r in flat}):
        keys = [key for key in common if key[1] == model]
        results = {}
        for method in METHODS:
            rows = [lookup[(*key, method)] for key in keys]
            pairs = [{**r, "control": lookup[(r["sample_id"], model, "original")]["correct"]} for r in rows]
            results[method] = {"n": len(rows), "correct": sum(r["correct"] for r in rows), "accuracy": float(np.mean([r["correct"] for r in rows])), "repairs": sum(r["control"] == 0 and r["correct"] == 1 for r in pairs), "damage": sum(r["control"] == 1 and r["correct"] == 0 for r in pairs), "vs_original": cluster_bootstrap(pairs, "correct", "control")}
        readers[model] = results
    candidate = records("results/kbs_natural_v1/candidate_records") + records("results/kbs_natural_boolq_v1/candidate_records")
    labels = Counter(r["labels"].get("model", "missing") for r in candidate)
    valid = sum(bool(r["labels"].get("ok")) for r in candidate)
    report = {"scope": "Saved result JSON only, excluding caches and quarantine; root model fields count record objects, NOT calls or independent samples.", "inventory_by_stage": dict(inventory), "gemini_screening": {"questions": len(screen), "baseline_success": sum(bool(v.get("ok")) for v in baseline), "baseline_planned": len(baseline), "support_success": sum(bool(v.get("ok")) for v in support), "support_planned": len(support)}, "gemini_controlled": {"planned_records": len(order), "complete_records": sum(all(v.get("ok") for v in r["variants"].values()) for r in order), "successful_conditions": sum(bool(v.get("ok")) for v in order_calls), "planned_conditions": len(order_calls)}, "gemini_natural": stages, "ranking_common_by_reader": readers, "gemini_ranking_answer_conditions": {"planned": sum(len(r["conditions"]) for r in raw if r["model"] == GEMINI), "success": sum(bool(v.get("ok")) for r in raw if r["model"] == GEMINI for v in r["conditions"].values())}, "candidate_labelers": dict(labels), "valid_candidate_labels": valid, "excluded_from_confirmatory_evidence": {"probes": "Connectivity and schema tests are not benchmark evaluations.", "screening": "Defines eligibility; not a fresh evaluation replicate.", "candidate_labels": "Evaluation annotations, not independent reader models.", "older_pilots": "Different questions, protocols and exploratory selection; not pooled as extra confirmation.", "gemini_robustness": "Not run: wording/distractor and controlled-repeat subsets have four endpoints."}}
    (ROOT / "analysis/model_coverage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (ROOT / "analysis/model_coverage_input_hashes.json").write_text(json.dumps(INPUTS, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("inventory_by_stage", "ranking_common_by_reader")}, indent=2))
    print("COMMON READER RESULTS", json.dumps(readers, indent=2))


if __name__ == "__main__":
    main()
