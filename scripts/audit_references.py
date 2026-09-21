"""Check bibliography fields against retained metadata and inspect citation scope."""
from __future__ import annotations

import json
import re
from pathlib import Path

import bibtexparser
from bs4 import BeautifulSoup
from pylatexenc.latex2text import LatexNodes2Text
import requests

from collect_references import normalized

ROOT = Path(__file__).resolve().parents[1]


def expand(path):
    text = path.read_text(encoding="utf-8")
    return re.sub(r"\\input\{([^}]+)\}", lambda m: expand(ROOT / (m[1] if m[1].endswith(".tex") else m[1] + ".tex")), text)


def main():
    library = bibtexparser.parse_string((ROOT / "references.bib").read_text(encoding="utf-8"))
    if library.failed_blocks:
        raise ValueError(f"Unparsed BibTeX blocks: {library.failed_blocks}")
    entries = [{"ID": e.key, **{k: field.value for k, field in e.fields_dict.items()}} for e in library.entries]
    metadata = {r["key"]: r for r in json.loads((ROOT / "sources/reference_verification.json").read_text(encoding="utf-8")) if r["status"] == "verified"}
    text = expand(ROOT / "main.tex") + expand(ROOT / "supplement.tex")
    cited = {k.strip() for block in re.findall(r"\\cite\w*\{([^}]+)\}", text) for k in block.split(",")}
    decoder = LatexNodes2Text()
    checks = []
    abstracts = []
    new_keys = {"kwiatkowski2019nq", "joshi2017triviaqa", "yang2018hotpotqa", "thorne2018fever", "petroni2021kilt", "schuster2021vitaminc", "mallen2023trust", "yoran2024robust", "gao2023alce", "trivedi2023ircot", "saad2024ragbench", "li2024longcontext", "liu2023verifiability", "chen2022murag", "wang2025conflicting", "wan2024convincing", "wang2024astute", "ming2024faitheval"}
    for entry in entries:
        key = entry["ID"]; source = metadata[key]["metadata"]
        title = decoder.latex_to_text(entry["title"])
        authors = entry["author"].split(" and ")
        expected_year = str(source.get("published", source.get("issued"))["date-parts"][0][0])
        fields = {"title": normalized(title) == normalized(source["title"][0]), "doi": entry["doi"].casefold() == source["DOI"].casefold(), "year": entry["year"] == expected_year, "author_count": len(authors) == len(source["author"]), "cited": key in cited}
        expected_authors = [a.get("family", a.get("name", "")) + (", " + a["given"] if a.get("given") else "") for a in source["author"]]
        fields["author_names_and_order"] = [normalized(decoder.latex_to_text(a)) for a in authors] == [normalized(a) for a in expected_authors]
        container = source.get("container-title", [])
        fields["venue_or_explicit_preprint"] = normalized(decoder.latex_to_text(entry.get("journal", entry.get("booktitle", "")))) == normalized(container[0]) if container else "arXiv preprint" in entry.get("howpublished", "")
        for bib_field, source_field in (("volume", "volume"), ("number", "issue"), ("pages", "page")):
            fields[bib_field] = normalized(decoder.latex_to_text(entry.get(bib_field, ""))) == normalized(str(source.get(source_field, "")))
        checks.append({"key": key, "passed": all(fields.values()), "fields": fields})
        if key not in new_keys: continue
        doi = entry["doi"]
        if source.get("abstract"):
            abstract = BeautifulSoup(source["abstract"], "html.parser").get_text(" ", strip=True)
            abstracts.append({"key": key, "url": "https://api.crossref.org/works/" + doi, "abstract": abstract, "status": "retained_publisher_abstract"})
            continue
        url = "https://aclanthology.org/" + doi.split("/v1/")[1] + "/" if "/v1/" in doi else "https://arxiv.org/abs/" + doi.split("arXiv.")[-1] if "arXiv." in doi else "https://doi.org/" + doi
        url = re.sub(r"aclanthology.org/([a-z])([0-9]{2}-)", lambda m: "aclanthology.org/" + m[1].upper() + m[2], url)
        target = ROOT / "sources" / "reference_abstracts" / (key + ".html")
        target.parent.mkdir(exist_ok=True)
        try:
            if not target.exists():
                response = requests.get(url, timeout=25); response.raise_for_status(); target.write_text(response.text, encoding="utf-8")
            soup = BeautifulSoup(target.read_text(encoding="utf-8"), "html.parser")
            node = soup.select_one("#abstract") or soup.select_one(".abstract") or soup.select_one(".acl-abstract")
            abstract = node.get_text(" ", strip=True) if node else ""
            abstracts.append({"key": key, "url": url, "abstract": abstract, "status": "retrieved" if abstract else "metadata_only"})
        except requests.RequestException as error:
            abstracts.append({"key": key, "url": url, "status": type(error).__name__})
    keys = [e["ID"] for e in entries]
    dois = [e["doi"].casefold() for e in entries]
    report = {"references": len(entries), "passed": all(c["passed"] for c in checks) and len(keys) == len(set(keys)) and len(dois) == len(set(dois)) and set(keys) == cited, "all_cited": set(keys) == cited, "unique_dois": len(dois) == len(set(dois)), "checks": checks, "limits": "Metadata and citation-context audit, not a claim of exhaustive full-text peer review. Explicit arXiv versions retain their preprint year."}
    (ROOT / "sources/reference_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (ROOT / "sources/new_reference_abstracts.json").write_text(json.dumps(abstracts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print("ABSTRACTS", json.dumps(abstracts, ensure_ascii=False, indent=2))
    if not report["passed"]: raise SystemExit(1)


if __name__ == "__main__": main()
