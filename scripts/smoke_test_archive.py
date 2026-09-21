"""Rebuild the source archive in isolation and compare figures and PDF content."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

import fitz

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pdf_text(path):
    with fitz.open(path) as document:
        return [page.get_text() for page in document]


def main():
    archive = ROOT / "output/kbs_manuscript_source.zip"
    target = Path(tempfile.mkdtemp(prefix="journal_smoke_", dir=ROOT / "qa"))
    with ZipFile(archive) as source:
        for name in source.namelist():
            if not (target / name).resolve().is_relative_to(target.resolve()):
                raise ValueError(f"Invalid archive member: {name}")
        source.extractall(target)
    manifest = json.loads((target / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert all(digest(target / name) == detail["sha256"] for name, detail in manifest["files"].items())
    report = {"archive_sha256": digest(archive), "directory": str(target.relative_to(ROOT)), "manifest_verified": True, "commands": []}
    for script, options in (("make_figures.py", []), ("make_followup_figures.py", []),
                            ("build_paper.py", []), ("validate_package.py", ["--package-only"])):
        command = [sys.executable, "-X", "utf8", "scripts/" + script, *options]
        result = subprocess.run(command, cwd=target, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
        (target / "qa" / (script + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        report["commands"].append({"script": script, "exit_code": result.returncode})
        print(script, "exit", result.returncode, flush=True)
        if result.returncode:
            print((result.stdout + result.stderr)[-6000:])
            raise RuntimeError(f"Archive rebuild failed: {script}")
    report["figure_png_hashes_match"] = {p.name: digest(p) == digest(target / "figures_revision" / p.name) for p in (ROOT / "figures_revision").glob("*.png")}
    report["pdf_text_matches"] = {name: pdf_text(ROOT / "output/pdf" / name) == pdf_text(target / "output/pdf" / name) for name in ("manuscript.pdf", "supplement.pdf")}
    report["pdf_pages"] = {name: len(pdf_text(target / "output/pdf" / name)) for name in ("manuscript.pdf", "supplement.pdf")}
    validation = json.loads((target / "qa/validation_report.json").read_text(encoding="utf-8"))
    report["package_validation_checks"] = len(validation["checks"])
    report["passed"] = validation["passed"] and all(report["figure_png_hashes_match"].values()) and all(report["pdf_text_matches"].values())
    report["scope"] = "Build-source isolation and artifact equality; not independent scientific replication. A later documentation-only repackage may change the archive hash."
    (ROOT / "qa/source_archive_smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
