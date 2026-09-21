"""Validate paper artifacts; full checks require the original project tree."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import fitz
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def expanded_tex(path):
    text = path.read_text(encoding="utf-8")
    return re.sub(r"\\input\{([^}]+)\}", lambda m: expanded_tex(ROOT / (m[1] if m[1].endswith(".tex") else m[1] + ".tex")), text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-only", action="store_true")
    args = parser.parse_args()
    checks = []

    def check(name, condition, detail=None):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    main_text = expanded_tex(ROOT / "main.tex")
    supp = expanded_tex(ROOT / "supplement.tex")
    bib = (ROOT / "references.bib").read_text(encoding="utf-8")
    keys = re.findall(r"@\w+\{([^,]+),", bib)
    cited = {k.strip() for block in re.findall(r"\\cite\w*\{([^}]+)\}", main_text + supp) for k in block.split(",")}
    verified = json.loads((ROOT / "sources/reference_verification.json").read_text(encoding="utf-8"))
    valid_keys = {r["key"] for r in verified if r["status"] == "verified"}
    check("at least 60 unique, cited, metadata-verified references", len(keys) == len(set(keys)) >= 60 and set(keys) == cited and cited <= valid_keys, len(keys))
    ref_audit = json.loads((ROOT / "sources/reference_audit.json").read_text(encoding="utf-8"))
    check("structured bibliography field and DOI audit passes", ref_audit["passed"] and ref_audit["references"] == len(keys))
    bbl_keys = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", (ROOT / "build/main.bbl").read_text(encoding="utf-8"))
    check("compiled bibliography contains every cited entry once", len(bbl_keys) == len(keys) and set(bbl_keys) == set(keys))
    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", main_text, re.S).group(1)
    check("abstract <=250 whitespace-separated words and no citations", len(abstract.split()) <= 250 and "\\cite" not in abstract, len(abstract.split()))
    check("title and abstract state the three-gate contribution",
          "A three-gate evaluation framework" in main_text
          and "three-gate evaluation framework" in abstract)
    check("no unresolved drafting tokens", not re.search(r"\b(?:TODO|FIXME|TBD|INSERT HERE)\b", main_text + supp))
    check("six focused main figures and three supplementary diagnostics",
          main_text.count("\\includegraphics") == 6 and supp.count("\\includegraphics") == 3)
    check("procedural pseudocode moved from main text to supplement",
          main_text.count("\\begin{algorithm") == 0 and supp.count("\\begin{algorithm}") == 2)
    figures = sorted((ROOT / "figures_revision").glob("*.pdf"))
    check("ten vector figures and ten PNG previews", len(figures) == 10 and len(list((ROOT / "figures_revision").glob("*.png"))) == 10)
    for name in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", main_text + supp):
        check("included figure exists: " + name, (ROOT / "figures_revision" / name).is_file())
    for path in figures:
        with fitz.open(path) as doc:
            check("nonblank figure: " + path.stem, len(doc) == 1 and len(doc[0].get_text()) > 15 and path.with_suffix(".png").stat().st_size > 1000)
    highlights = (ROOT / "highlights.txt").read_text(encoding="utf-8").splitlines()
    check("highlights 3-5 bullets, each <=85 characters", 3 <= len(highlights) <= 5 and all(len(s) <= 85 for s in highlights), [len(s) for s in highlights])
    with ZipFile(ROOT / "highlights.docx") as z:
        doc = ET.fromstring(z.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = ["".join(p.itertext()) for p in doc.findall(".//w:p", ns)]
    check("DOCX highlights match text source", paragraphs == ["Highlights", *highlights])
    human_protocol = (ROOT / "HUMAN_ANNOTATION_PROTOCOL.md").read_text(encoding="utf-8")
    controlled_template = (ROOT / "human_annotation/controlled_annotation_blank.csv").read_text(encoding="utf-8").splitlines()
    natural_template = (ROOT / "human_annotation/natural_candidate_annotation_blank.csv").read_text(encoding="utf-8").splitlines()
    check("human protocol is prospective and explicitly unexecuted",
          "annotation has not been performed" in human_protocol
          and "No human labels are used in the reported analyses" in supp
          and "no human-derived estimate" in main_text.lower())
    check("human annotation CSV templates are blank and structurally complete",
          len(controlled_template) == len(natural_template) == 1
          and all(field in controlled_template[0] for field in ("case_id", "annotator_id", "support_label", "support_quote", "foil_label", "foil_quote"))
          and all(field in natural_template[0] for field in ("case_id", "candidate_id", "annotator_id", "candidate_label", "evidence_quote")))
    report = json.loads((ROOT / "qa/compile_report.json").read_text(encoding="utf-8"))
    for stem, name in (("main", "manuscript"), ("supplement", "supplement")):
        log = (ROOT / f"build/{stem}.log").read_text(encoding="utf-8", errors="replace")
        check(stem + " no undefined references or fatal errors", not re.search(r"undefined|Fatal error|Emergency stop|Rerun to get", log, re.I))
        item = report["pdfs"][stem]
        check(stem + " no text outside PDF page", not item["outside_page_text"])
        # The supplied CAS class deliberately places its keyword box in a zero-width box.
        other_warnings = [s for s in item["warnings"] if not s.startswith("Overfull \\hbox (123.62721pt too wide) detected") and not s.startswith("Package hyperref Warning: Ignoring empty anchor")]
        check(stem + " no unresolved compile warnings beyond reviewed CAS first-page warnings", not other_warnings, item["warnings"])
        with fitz.open(ROOT / f"output/pdf/{name}.pdf") as doc:
            check(stem + " page count matches compile report", len(doc) == len(item["pages"]), len(doc))
            check(stem + " no blank pages", all(len(p.get_text().strip()) > 50 for p in doc))
            if stem == "main":
                check("main remains within a 25-page CAS submission envelope", len(doc) <= 25, len(doc))
                reference_pages = [i + 1 for i, p in enumerate(doc) if "\nReferences\n" in p.get_text()]
                check("references follow at least 14 pages of main text", bool(reference_pages) and min(reference_pages) >= 15, reference_pages)
                check("main footer total matches document", all(f"Page {i+1} of {len(doc)}" in p.get_text() for i, p in enumerate(doc)))
    result = json.loads((ROOT / "analysis/paper_results.json").read_text(encoding="utf-8"))
    primary = result["controlled"]["primary"]
    old = result["controlled"]["legacy_primary"]
    check("1152 records and 386 unique questions", result["controlled"]["records"] == 1152 and result["controlled"]["questions"] == 386)
    check("primary point estimates preserved", all(np.isclose(primary[a]["difference"], old[b]["difference"], atol=1e-14) for a, b in (("stable_correct", "stable_correct"), ("support_rescuable", "support_rescuable"), ("interaction", "dependency_interaction"))))
    check("primary interaction equals stratum difference", np.isclose(primary["interaction"]["difference"], primary["support_rescuable"]["difference"] - primary["stable_correct"]["difference"]))
    binary = json.loads((ROOT / "analysis/binary_complement_summary.json").read_text(encoding="utf-8"))
    binary_pooled = binary["pooled"]
    check("binary-complement intervention has 558 complete records and 2232 successful slots",
          binary["scope"]["planned_records"] == binary["scope"]["complete_records"] == 558
          and binary["completeness"]["planned_calls"] == 2232
          and binary["completeness"]["missing_records"] == 0
          and binary["completeness"]["incomplete_observed_records"] == 0
          and binary["completeness"]["failed_or_missing_observed_slots"] == 0)
    check("binary interaction reconstructs and matches manuscript",
          np.isclose(binary_pooled["interaction"]["difference"],
                     binary_pooled["support_rescuable"]["difference"]
                     - binary_pooled["stable_correct"]["difference"])
          and np.isclose(binary_pooled["interaction"]["difference"], 0.13029149159663866)
          and "13.03" in main_text and "7.58" in main_text and "18.40" in main_text)
    check("binary-complement study reports both tasks and endpoint heterogeneity",
          set(binary["by_dataset"]) == {"BoolQ", "StrategyQA"}
          and len(binary["by_model"]) == 4
          and all(value["ci95"][0] > 0
                  for value in binary["leave_one_model_out"].values())
          and ("does not randomize" in main_text or "neither randomizes" in main_text or "nonrandomized" in main_text))
    check("600 natural questions and 2986 complete records", result["natural"]["overall"]["net"]["questions"] == 600 and result["natural"]["overall"]["net"]["n"] == 2986)
    check("all seven credibility-control intervals include zero", len(result["reranking"]["paired_against_all_controls"]) == 7 and all(r["ci95"][0] <= 0 <= r["ci95"][1] for r in result["reranking"]["paired_against_all_controls"].values()))
    revision = json.loads((ROOT / "analysis/revision_diagnostics.json").read_text(encoding="utf-8"))
    follow = json.loads((ROOT / "analysis/followup_results.json").read_text(encoding="utf-8"))
    audit = follow["audit"]
    foil = audit["foil"]
    check("historical Sol audit complete and relation counts reconcile", foil["valid_pass_requests"] == 148 and sum(foil["stable_relations"].values()) + foil["case_status"]["disputed"] == foil["planned_unique_cases"] == 591)
    strict = foil["controlled_sensitivity"]
    check("historical Sol subset retains 890 records and 325 questions", strict["stable_correct"]["n"] == 509 and strict["support_rescuable"]["n"] == 381 and foil["strict_valid_records"] == 890 and strict["interaction"]["questions"] == 325)
    check("historical Sol interaction reconstructs from strata", np.isclose(strict["interaction"]["difference"], strict["support_rescuable"]["difference"] - strict["stable_correct"]["difference"]))
    check("historical Sol natural audit retains 34 old pairs", audit["natural"]["old_pairs_with_two_valid_passes"] == 70 and audit["natural"]["old_pairs_strictly_retained"] == 34 and audit["natural"]["set_status"]["both_valid"] == 159)
    cross = json.loads((ROOT / "analysis/cross_family_summary.json").read_text(encoding="utf-8"))
    cross_agreement = json.loads((ROOT / "analysis/cross_family_agreement.json").read_text(encoding="utf-8"))
    cross_sensitivity = json.loads((ROOT / "analysis/cross_family_sensitivity.json").read_text(encoding="utf-8"))
    cross_invalid = json.loads((ROOT / "analysis/cross_family_invalid_slots.json").read_text(encoding="utf-8"))
    expected_cross_hashes = {
        "cross_family_accounting.json": "5bd40c9c5e4cdce5d3d3e701b79154f77cfac721b21b3bf12d0748eefffe3930",
        "cross_family_agreement.json": "d076337a2093db98e768b76a3ec15975793204a5a1994258f7f73948cdf03c73",
        "cross_family_invalid_slots.json": "900e8817fc0df7feb6572c5f281581ace4f85edcc6ff0587e7aa2b871ab335dc",
        "cross_family_sensitivity.json": "74c5571af46aa7318eaae4b5cf17a85f20c83c65a25436d0817854140d5ef294",
        "cross_family_summary.json": "63e6d77a6fdc0f8604af52475a57a0052d1354f5d13a555d1c07a043ad81b477",
    }
    check("cross-family analysis copies match frozen SHA-256 values",
          all(hashlib.sha256((ROOT / "analysis" / name).read_bytes()).hexdigest() == digest
              for name, digest in expected_cross_hashes.items()))
    check("cross-family audit is partial with 3956 of 3966 valid slots",
          cross["status"] == "partial" and cross["inventory"] == {"planned": 3966, "saved": 3966, "valid": 3956, "recovery_used": 64, "invalid": 10}
          and cross_invalid["count"] == 10 and "3,956/3,966" in (main_text + supp))
    check("cross-family manifest and raw aggregate hashes are disclosed",
          cross["integrity"]["manifest_sha256"] == "435ef45dd4e283503f4acea77bfb1cfb95496b4b160f5e955824d901a8d7023d"
          and cross["integrity"]["raw_aggregate_sha256"] == "9aa3bd2c2c6fff52d4efa20b3d4c57e8984656d2353378e0dc6b4f2d247c9788"
          and cross["integrity"]["raw_files"] == 4030)
    check("three-family original-presentation agreement matches corrected analysis",
          np.isclose(cross_agreement["controlled"]["raw_three_of_three_agreement"], 0.9063032367972743)
          and np.isclose(cross_agreement["natural"]["raw_three_of_three_agreement"], 0.75)
          and np.isclose(cross_agreement["controlled"]["fleiss_kappa"], 0.9004896270704101)
          and np.isclose(cross_agreement["natural"]["gwet_ac1"], 0.7896388800774663))
    check("all three judges exceed 92 percent position stability",
          set(cross["model_diagnostics"]) == {"gpt-6-astra", "claude-opus-5", "grok-4.6"}
          and all(v["position_stability_rate_among_two_valid"] > .92 for v in cross["model_diagnostics"].values()))
    tier_a = cross_sensitivity["tier_a_strict"]
    tier_effect = tier_a["controlled_sensitivity"]
    check("Tier A retains 267 controlled cases and 27 natural pairs",
          tier_a["controlled_cases"] == 267 and tier_a["controlled_records"] == 713
          and tier_a["natural_cases"] == 27 and tier_a["natural_sensitivity"]["records"] == 133
          and cross["case_flow"]["controlled"]["tier_a_strict_cases"] == 267
          and cross["case_flow"]["natural"]["tier_a_strict_cases"] == 27)
    check("Tier A controlled interaction reconstructs and matches manuscript",
          tier_effect["stable_correct"]["n"] == 431 and tier_effect["support_rescuable"]["n"] == 282
          and tier_effect["interaction"]["questions"] == 260
          and np.isclose(tier_effect["interaction"]["difference"], tier_effect["support_rescuable"]["difference"] - tier_effect["stable_correct"]["difference"])
          and np.isclose(tier_effect["interaction"]["difference"], 0.1347970248967435)
          and "13.48" in (main_text + supp) and "8.86" in (main_text + supp) and "17.86" in (main_text + supp))
    check("all prespecified automatic subsets remain positive with intervals above zero",
          all(v["controlled_sensitivity"]["interaction"]["ci95"][0] > 0
                  and v["natural_sensitivity"]["ci95"][0] > 0
              for v in cross_sensitivity.values()))
    check("paper distinguishes automatic audit from human validation and authenticated checkpoints",
          "not human validation or ground truth" in main_text
          and "does not independently authenticate" in supp
          and "No human labels are used in the reported analyses" in supp)
    check("NQ candidate audit explicitly partial", audit["nq"]["status"] == "partial" and audit["nq"]["set_status"]["both_valid"] == 98 and "candidate audit was interrupted nonrandomly after 98 sets" in main_text)
    screen = follow["screen"]
    check("Gemini follow-up separate and all 150 records complete", screen["status"] == "complete" and screen["order_complete_records"] == 150 and "complement" in main_text and "2.68" in (main_text + supp))
    for task, cells in screen["order_analysis"]["cells"].items():
        for stratum, v in cells.items():
            a = v["accuracy"]
            check(f"{task} {stratum} order contrast reconstructed", np.isclose(v["order_effect"]["difference"], (a["top_sf"]-a["top_fs"]+a["bottom_sf"]-a["bottom_fs"])/2))
    check("NQ 200 question-only snapshots; three-endpoint pool withheld", follow["nq"]["query_only_verified"] and follow["nq"]["six_candidates"] == 200 and follow["nq"]["frozen_three_model_pooled"]["status"] == "withheld_until_complete")
    for model, value in follow["nq"]["by_model"].items():
        v = value["complete"]
        check(model + " NQ repair and change accounting", np.isclose(v["accuracy"]["original"]-v["accuracy"]["baseline"], (v["repairs"]-v["damage"])/v["records"]) and v["changed_answers"] == v["changed_but_all_wrong"]+v["changed_correctness"]+v["changed_but_all_correct"])
    check("NQ 2988 successful slots and 594 complete records disclosed", sum(v["successful_conditions"] for v in follow["nq"]["by_model"].values()) == 2988 and sum(v["complete"]["records"] for v in follow["nq"]["by_model"].values()) == 594)
    check("all 3360 independent audit consistency checks passed", follow["audit_record_validation"]["passed"] and follow["audit_record_validation"]["total_checks"] == 3360)
    check("obsolete no-independent-audit assertions removed", "No additional independent LLM audit" not in main_text and "No human annotation or new independent LLM audit" not in supp)
    coverage = json.loads((ROOT / "analysis/model_coverage.json").read_text(encoding="utf-8"))
    check("Gemini coverage is explicit and reconciles", coverage["gemini_controlled"]["complete_records"] == 189 and sum(v["complete_records"] for v in coverage["gemini_natural"].values()) == 586 and coverage["ranking_common_by_reader"]["gemini-3.8-flash"]["original"]["n"] == 291 and "The Gemini extension" in main_text)
    for method, pooled in revision["ranking"]["common_complete"].items():
        rows = [v[method] for v in coverage["ranking_common_by_reader"].values()]
        check(method + " reader-specific results reconstruct pooled outcome", sum(r["n"] for r in rows) == pooled["n"] and np.isclose(sum(r["correct"] for r in rows)/pooled["n"], pooled["accuracy"]) and sum(r["repairs"] for r in rows) == pooled["vs_original"]["counts"]["01"] and sum(r["damage"] for r in rows) == pooled["vs_original"]["counts"]["10"])

    def transition_valid(v):
        c, n = v["counts"], v["n"]
        return sum(c.values()) == n and np.isclose(v["net"], (c["01"]-c["10"])/n) and np.isclose(v["gross"], (c["01"]+c["10"])/n)

    for stratum, v in revision["controlled"]["strata"].items():
        check(stratum + " signatures reconstruct four accuracies", sum(v["signatures"].values()) == v["n"] and all(np.isclose(sum(int(sig[j])*count for sig, count in v["signatures"].items())/v["n"], v["accuracy"][order]) for j, order in enumerate(("top_sf", "top_fs", "bottom_sf", "bottom_fs"))))
        check(stratum + " swap accounting and primary estimate agree", transition_valid(v["swaps"]) and v["swaps"]["n"] == 2*v["n"] and np.isclose(v["swaps"]["net"], primary[stratum]["difference"]))
    clean = revision["controlled"]["nonanswer_sensitivity"]
    check("47 nonanswer exclusions and 590 retained rescuable records", clean["excluded"] == 47 and clean["excluded_by_foil"] == {"abstain": 47} and clean["primary"]["support_rescuable"]["n"] == 590 and np.isclose(clean["primary"]["interaction"]["difference"], clean["primary"]["support_rescuable"]["difference"]-clean["primary"]["stable_correct"]["difference"]))
    for name, v in revision["controlled"]["voting"].items():
        key = "vote" if name == "permutation" else "sc"
        check(name + " voting categories reproduce saved accuracy", sum(v["counts"].values()) == v["n"] == 558 and np.isclose(v["counts"]["correct"]/v["n"], result["controlled_mitigation"][key]["difference"]) and 0 <= v["success_available_but_lost"] <= v["n"]-v["counts"]["correct"])
    for task, v in revision["natural"]["tasks"].items():
        check(task + " natural transitions and normalization are coherent", transition_valid(v["transition"]) and transition_valid(v["original_reverse"]) and v["scoring_normalization_conflicts"] == 0 and sum(v["categories"].values()) == sum(v["success_count"].values()) == v["n"])
        check(task + " observed order envelope identity holds", np.isclose(v["observed_best"]-v["observed_worst"], v["categories"]["correctness_changes"]/v["n"]) and v["observed_worst"] <= v["original_accuracy"] <= v["observed_best"] and np.isclose(v["original_accuracy"]-v["baseline_accuracy"], v["transition"]["net"]))
        check(task + " candidate coverage and conflict transitions reconcile", sum(revision["natural"]["candidate_coverage"][task]["counts"].values()) == revision["natural"]["candidate_coverage"][task]["n"] and transition_valid(revision["natural"]["conflict_pairs"][task]))
        counts = v["transition"]["counts"]
        expected = " & ".join(map(str, [task, v["n"], counts["01"], counts["10"], v["n"]-v["categories"]["invariant"], v["categories"]["correctness_changes"], f"{100*v['original_accuracy']:.1f}", f"{100*v['observed_best']:.1f}"]))
        check(task + " manuscript accounting table matches diagnostics", expected in main_text)
    for method, v in revision["ranking"]["permutations"].items():
        check(method + " inversion distribution reconciles", len(v["inversions"]) == v["n"] == 300 and all(0 <= x <= 15 for x in v["inversions"]) and v["inversions"].count(0) == v["unchanged"] and np.isclose(np.mean(v["inversions"]), v["mean_inversions"]) and v["fallback"] <= v["unchanged"])
    baseline = revision["ranking"]["common_complete"]["original"]["accuracy"]
    for method, v in revision["ranking"]["common_complete"].items():
        check(method + " common-set transitions reproduce accuracy", v["n"] == 591 and transition_valid(v["vs_original"]) and np.isclose(v["accuracy"]-baseline, v["vs_original"]["net"]) and np.isclose(v["accuracy"], result["reranking"]["common_complete_accuracy"][method]))
        if method not in ("random", "reverse"):
            counts = v["vs_original"]["counts"]
            expected = " & ".join([f"{100*v['accuracy']:.2f}", str(counts["01"]), str(counts["10"]), f"{v['answer_calls']:,}", f"{v['answer_tokens']:,}"])
            check(method + " manuscript activity table matches diagnostics", expected in main_text)
    groups = revision["ranking"]["distance_groups"]
    check("distance groups partition 591 common records and all transitions", sum(v["n"] for v in groups.values()) == 591 and all(transition_valid(v) for v in groups.values()) and all(sum(v["counts"][c] for v in groups.values()) == revision["ranking"]["common_complete"]["credibility"]["vs_original"]["counts"][c] for c in ("00", "01", "10", "11")))
    for v in revision["controlled"]["cases"]:
        check("case traced to saved signature: " + v["entry_id"], v["question"] in (main_text + supp) and "".join(str(int(v["answers"][o] == v["support"])) for o in ("top_sf", "top_fs", "bottom_sf", "bottom_fs")) == v["signature"])
    if not args.package_only:
        binary_plan = ROOT.parent / "data/kbs_binary_complement_v1.json"
        binary_freeze = ROOT.parent / "data/kbs_binary_complement_v1.json.sha256"
        observed = hashlib.sha256(binary_plan.read_bytes()).hexdigest()
        expected = binary_freeze.read_text(encoding="ascii").split()[0]
        check("binary-complement plan still matches frozen SHA-256",
              observed == expected == "72a71a5d06b410a7bd00e815d315a91f61e224a22f05bb248bb4841b087efa8e")
        follow_hashes = json.loads((ROOT / "analysis/followup_input_hashes.json").read_text(encoding="utf-8"))
        changed = [name for name, expected in follow_hashes.items() if not (ROOT.parent / name).is_file() or hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest() != expected]
        check("all follow-up analysis inputs unchanged", not changed, {"checked": len(follow_hashes), "changed": changed})
        hashes = json.loads((ROOT / "analysis/input_hashes.json").read_text(encoding="utf-8"))
        changed = [name for name, expected in hashes.items() if not (ROOT.parent / name).is_file() or hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest() != expected]
        check("all original analysis inputs unchanged", not changed, {"checked": len(hashes), "changed": changed})
        revision_hashes = json.loads((ROOT / "analysis/revision_input_hashes.json").read_text(encoding="utf-8"))
        changed = [name for name, expected in revision_hashes.items() if not (ROOT.parent / name).is_file() or hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest() != expected]
        check("all revision analysis inputs unchanged", not changed, {"checked": len(revision_hashes), "changed": changed})
        coverage_hashes = json.loads((ROOT / "analysis/model_coverage_input_hashes.json").read_text(encoding="utf-8"))
        changed = [name for name, expected in coverage_hashes.items() if not (ROOT.parent / name).is_file() or hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest() != expected]
        check("all model coverage analysis inputs unchanged", not changed, {"checked": len(coverage_hashes), "changed": changed})
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_evidence import bootstrap
        rows = [{"qid": str(i), "delta": d} for i, d in enumerate((-1, 0, 0, 1, 1, 1))]
        a, b = bootstrap(rows)["delta"], bootstrap(rows * 5)["delta"]
        check("duplicating same-question model rows does not narrow CI", a["difference"] == b["difference"] and a["ci95"] == b["ci95"] and a["questions"] == b["questions"])
        joint = bootstrap([{"qid": str(i), "a": d, "b": d} for i, d in enumerate((-1, 0, 1, 1))], ("a", "b"))
        check("joint strata use identical question draws", joint["interaction"]["ci95"] == [0., 0.] and joint["interaction"]["difference"] == 0)
        from analyze_revision import transition, inversions
        synthetic = transition([(0, 1), (1, 0), (0, 1), (1, 1)])
        check("synthetic transition and permutation boundary tests", transition_valid(synthetic) and synthetic["net"] == .25 and synthetic["gross"] == .75 and inversions(["E1", "E2", "E3", "E4", "E5", "E6"]) == 0 and inversions(["E6", "E5", "E4", "E3", "E2", "E1"]) == 15)
    passed = all(c["passed"] for c in checks)
    output = {"passed": passed, "mode": "package-only" if args.package_only else "full-project", "checks": checks, "limitations": ["Automated checks do not replace scientific or visual review.", "The supplied CAS zero-width keyword-box warning is visually reviewed, not a page overflow."]}
    (ROOT / "qa/validation_report.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    for c in checks:
        print(("PASS " if c["passed"] else "FAIL ") + c["name"])
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
