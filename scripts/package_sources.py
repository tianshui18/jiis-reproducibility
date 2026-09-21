"""Package an explicit allowlist; exclude credentials and model-request caches."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent


def main():
    validation = json.loads((ROOT / "qa/validation_report.json").read_text(encoding="utf-8"))
    if not validation["passed"]:
        raise RuntimeError("Validation must pass before packaging")
    names = ["main.tex", "supplement.tex", "references.bib", "highlights.docx", "highlights.txt", "title_page_template.tex", "README.md", "SUBMISSION_CHECKLIST.md", "HUMAN_ANNOTATION_PROTOCOL.md", "human_annotation/controlled_annotation_blank.csv", "human_annotation/natural_candidate_annotation_blank.csv", "cas-dc.cls", "cas-sc.cls", "cas-common.sty", "cas-model2-names.bst", "elsarticle-num.bst", "thumbnails/cas-email.jpeg", "analysis/paper_results.json", "analysis/input_hashes.json", "sources/reference_verification.json", "sources/policy_access.json", "qa/compile_report.json", "qa/validation_report.json", "qa/visual_review.json", "output/pdf/manuscript.pdf", "output/pdf/supplement.pdf"]
    names += ["analysis/revision_diagnostics.json", "analysis/revision_input_hashes.json"]
    names += ["analysis/followup_results.json", "analysis/followup_input_hashes.json"]
    names += ["analysis/cross_family_summary.json", "analysis/cross_family_agreement.json",
              "analysis/cross_family_sensitivity.json", "analysis/cross_family_accounting.json",
              "analysis/cross_family_invalid_slots.json"]
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT / "analysis/followup_audit").glob("*.json")]
    names += ["analysis/model_coverage.json", "analysis/model_coverage_input_hashes.json", "analysis/binary_complement_summary.json", "analysis/binary_complement_report.md", "sources/reference_audit.json", "sources/new_reference_abstracts.json"]
    files = {name: ROOT / name for name in names}
    files.update({"build/" + name: ROOT / "build" / name for name in ("main.log", "main.bbl", "supplement.log")})
    for folder, patterns in (("figures_revision", ("*.pdf", "*.png")), ("sections", ("*.tex",)), ("tables", ("*.tex",)), ("scripts", ("*.py", "*.ps1"))):
        for pattern in patterns:
            files.update({p.relative_to(ROOT).as_posix(): p for p in (ROOT / folder).glob(pattern)})
    protocols = ["order_confirmatory_screen_protocol.md", "order_confirmatory_protocol.md", "kbs_supplement_protocol_v1.md", "28_KBS自然任务与可信度排序冻结协议.md", "30_KBS论文撰写与统计复核记录.md", "31_KBS论文结构图表与洞见重构记录.md"]
    protocols += ["32_KBS图版文献与Gemini覆盖复核.md"]
    protocols += ["33_KBS独立审计补样与NQ冻结协议.md", "34_KBS独立审计补样与NQ执行结果.md",
                  "35_KBS独立审计OpenLux补充实验冻结协议.md", "36_KBS独立审计Claude替代冻结协议.md",
                  "37_KBS独立审计OpenLux补充实验结果.md", "38_KBS新增实验证据整合与论文修订.md"]
    protocols += ["39_KBS严格二元补集复制冻结协议.md"]
    protocols += ["40_KBS双模型零人工语义交叉验证实验计划.md", "41_KBS三模型零人工语义交叉验证实验结果.md"]
    files.update({"protocols/" + name: PROJECT / "docs" / name for name in protocols})
    experiment_files = [
        "dgms/kbs_binary_complement.py", "dgms/analyze_kbs_binary_complement.py",
        "dgms/order_confirmatory_runner.py", "scripts/prepare_kbs_binary_complement.py",
        "scripts/run_kbs_binary_complement.py", "scripts/analyze_kbs_binary_complement.py",
        "data/kbs_binary_complement_v1.json.sha256",
        "dgms/kbs_cross_family_audit.py", "scripts/prepare_kbs_cross_family_audit.py",
        "scripts/run_kbs_cross_family_audit.py", "scripts/analyze_kbs_cross_family_audit.py",
        "scripts/correct_kbs_cross_family_agreement.py",
    ]
    files.update({"experiment/" + name: PROJECT / name for name in experiment_files})
    audit_root = PROJECT / "results/kbs_cross_family_audit_v1"
    audit_files = ["manifest.json", "final_manifest.json", "source_hashes.json",
                   "frozen_cases.jsonl", "frozen_plan.jsonl"]
    files.update({"experiment/kbs_cross_family_audit_v1/" + name: audit_root / name for name in audit_files})
    for path in (audit_root / "prompts").rglob("*"):
        if path.is_file():
            files["experiment/kbs_cross_family_audit_v1/" + path.relative_to(audit_root).as_posix()] = path
    manifest = {"status": "author-identified submission draft; not submitted; human annotation protocol prepared but not executed", "date": "2026-09-21", "raw_data_included": False, "raw_data_note": "Reanalysis requires the original project tree; LaTeX and figures compile from this archive without it.", "python_packages": {name: importlib.metadata.version(name) for name in ("numpy", "matplotlib", "PyMuPDF", "Pillow", "requests", "bibtexparser", "beautifulsoup4", "pylatexenc")}, "files": {name: {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in sorted(files.items())}}
    manifest_path = ROOT / "output/artifact_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    target = ROOT / "output/kbs_manuscript_source.zip"
    with ZipFile(target, "w", ZIP_DEFLATED) as z:
        for name, path in sorted(files.items()):
            z.write(path, name)
        z.write(manifest_path, "artifact_manifest.json")
    with ZipFile(target) as z:
        assert z.testzip() is None
        for name, detail in manifest["files"].items():
            assert hashlib.sha256(z.read(name)).hexdigest() == detail["sha256"]
    print(f"Packaged {len(files)} files: {target} ({target.stat().st_size:,} bytes)")
    print("Archive SHA256:", hashlib.sha256(target.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
