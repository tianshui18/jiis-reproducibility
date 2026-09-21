"""Recompute the follow-up evidence without modifying any experimental records."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

PAPER = Path(__file__).resolve().parents[1]
PROJECT = PAPER.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PAPER / "scripts"))


def main():
    os.chdir(PROJECT)
    from scripts import analyze_kbs_followup as follow
    from scripts import analyze_kbs_independent_audit_results as audit
    from dgms.kbs_followup import load

    inputs = {}
    def tracked(path):
        p = Path(str(path).replace("\\", "/"))
        inputs[p.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
        return load(p)

    # Existing audit routines emit detailed views; redirect only those derived outputs.
    audit.load = tracked
    audit.OUT = PAPER / "analysis/followup_audit"
    report = {"date": "2026-09-19", "nq": follow.analyze_nq(),
              "screen": follow.analyze_screen(),
              "audit": {"foil": audit.foil_summary(),
                        "natural": audit.candidate_summary("natural"),
                        "nq": audit.candidate_summary("nq")}}
    report["audit_record_validation"] = audit.validate_records()
    assert report["audit_record_validation"]["passed"]
    saved = tracked("results/kbs_followup_v2/analysis/summary.json")
    assert report["nq"] == saved["nq"] and report["screen"] == saved["screen"]
    saved_audit = tracked("results/kbs_independent_audit_v3/analysis/summary.json")
    for stage, value in report["audit"].items():
        assert value == saved_audit["sol_v3"][stage], stage
    inputs.update(follow.INPUTS)
    for name in ("dgms/kbs_followup.py", "dgms/kbs_independent_audit.py",
                 "scripts/analyze_kbs_followup.py", "scripts/analyze_kbs_independent_audit_results.py",
                 "scripts/analyze_kbs_credibility.py", "dgms/analyze_order_confirmatory.py",
                 "paper/scripts/build_evidence.py"):
        inputs[name] = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    for name, value in (("followup_results", report), ("followup_input_hashes", inputs)):
        (PAPER / "analysis" / (name + ".json")).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Follow-up results reproduced; {len(inputs)} hashed inputs; "
          f"{report['audit_record_validation']['total_checks']} audit checks passed.")


if __name__ == "__main__":
    main()
