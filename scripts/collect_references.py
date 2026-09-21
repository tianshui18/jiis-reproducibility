"""Resolve relevant literature against Crossref; keep responses for verification."""
from __future__ import annotations

import concurrent.futures
import difflib
import html
import json
import re
import time
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
QUERIES = {
    "kwiatkowski2019nq": "Natural Questions: A Benchmark for Question Answering Research",
    "joshi2017triviaqa": "TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension",
    "yang2018hotpotqa": "HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering",
    "thorne2018fever": "FEVER: a Large-scale Dataset for Fact Extraction and VERification",
    "petroni2021kilt": "KILT: a Benchmark for Knowledge Intensive Language Tasks",
    "schuster2021vitaminc": "Get Your Vitamin C! Robust Fact Verification with Contrastive Evidence",
    "mallen2023trust": "When Not to Trust Language Models: Investigating Effectiveness of Parametric and Non-Parametric Memories",
    "yoran2024robust": "Making Retrieval-Augmented Language Models Robust to Irrelevant Context",
    "gao2023alce": "Enabling Large Language Models to Generate Text with Citations",
    "trivedi2023ircot": "Interleaving Retrieval with Chain-of-Thought Reasoning for Knowledge-Intensive Multi-Step Questions",
    "saad2024ragbench": "RAGBench: Explainable Benchmark for Retrieval-Augmented Generation Systems",
    "li2024longcontext": "Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach",
    "liu2023verifiability": "Evaluating Verifiability in Generative Search Engines",
    "chen2022murag": "MuRAG: Multimodal Retrieval-Augmented Generator for Open Question Answering over Images and Text",
    "lewis2020rag": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
    "karpukhin2020dpr": "Dense Passage Retrieval for Open-Domain Question Answering",
    "guu2020realm": "REALM: Retrieval-Augmented Language Model Pre-Training",
    "izacard2021fid": "Leveraging Passage Retrieval with Generative Models for Open Domain Question Answering",
    "izacard2023atlas": "Atlas: Few-shot Learning with Retrieval Augmented Language Models",
    "borgeaud2022retro": "Improving language models by retrieving from trillions of tokens",
    "gao2023survey": "Retrieval-Augmented Generation for Large Language Models: A Survey",
    "asai2024selfrag": "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
    "yan2024crag": "Corrective Retrieval Augmented Generation",
    "jiang2023flare": "Active Retrieval Augmented Generation",
    "shi2024replug": "REPLUG: Retrieval-Augmented Black-Box Language Models",
    "liu2024lost": "Lost in the Middle: How Language Models Use Long Contexts",
    "lu2022permutation": "Fantastically Ordered Prompts and Where to Find Them: Overcoming Few-Shot Prompt Order Sensitivity",
    "zhao2021calibrate": "Calibrate Before Use: Improving Few-Shot Performance of Language Models",
    "shi2023distracted": "Large Language Models Can Be Easily Distracted by Irrelevant Context",
    "longpre2021entity": "Entity-Based Knowledge Conflicts in Question Answering",
    "xie2024adaptive": "Adaptive Chameleon or Stubborn Sloth: Revealing the Behavior of Large Language Models in Knowledge Conflicts",
    "guzman2023faithful": "Faithful or Extractive? On Mitigating the Faithfulness-Abstractiveness Trade-off in Abstractive Summarization",
    "wu2024ragtruth": "RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models",
    "es2024ragas": "RAGAs: Automated Evaluation of Retrieval Augmented Generation",
    "saad2024ares": "ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems",
    "zheng2023judge": "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena",
    "liu2023geval": "G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment",
    "wang2024bias": "Large Language Models are not Fair Evaluators",
    "clark2019boolq": "BoolQ: Exploring the Surprising Difficulty of Natural Yes/No Questions",
    "geva2021strategyqa": "Did Aristotle Use a Laptop? A Question Answering Benchmark with Implicit Reasoning Strategies",
    "chen2023infoseek": "Can Pre-trained Vision and Language Models Answer Visual Information-Seeking Questions?",
    "hu2023oven": "Open-Domain Visual Entity Recognition: Towards Recognizing Millions of Wikipedia Entities",
    "wei2022cot": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
    "wang2023sc": "Self-Consistency Improves Chain of Thought Reasoning in Language Models",
    "sun2023rankgpt": "Is ChatGPT Good at Search? Investigating Large Language Models as Re-Ranking Agents",
    "nogueira2019rerank": "Passage Re-ranking with BERT",
    "robertson2009bm25": "The Probabilistic Relevance Framework: BM25 and Beyond",
    "khattab2020colbert": "ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT",
    "thakur2021beir": "BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models",
    "guo2017calibration": "On Calibration of Modern Neural Networks",
    "brier1950": "Verification of forecasts expressed in terms of probability",
    "efron1979": "Bootstrap Methods: Another Look at the Jackknife",
    "liang1986gee": "Longitudinal data analysis using generalized linear models",
    "dror2018testing": "The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing",
    "jia2017adversarial": "Adversarial Examples for Evaluating Reading Comprehension Systems",
    "petroni2019lama": "Language Models as Knowledge Bases?",
    "kandpal2023longtail": "Large Language Models Struggle to Learn Long-Tail Knowledge",
    "kadavath2022know": "Language Models (Mostly) Know What They Know",
    "ji2023hallucination": "Survey of Hallucination in Natural Language Generation",
    "huang2025hallucination": "A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions",
    "kbs2024design": "Retrieval augmented generation using engineering design knowledge",
    "kbs2026trustworthy": "Toward trustworthy engineering information extraction using retrieval-augmented generation",
    "wang2025conflicting": "Retrieval-Augmented Generation with Conflicting Evidence",
    "wan2024convincing": "What Evidence Do Language Models Find Convincing?",
    "wang2024astute": "Astute RAG: Overcoming Imperfect Retrieval Augmentation and Knowledge Conflicts for Large Language Models",
    "ming2024faitheval": "FaithEval: Can Your Language Model Stay Faithful to Context, Even If The Moon Is Made of Marshmallows?",
}

ARXIV = {
    "yoran2024robust": "2310.01558",
    "saad2024ragbench": "2407.11005",
    "lewis2020rag": "2005.11401", "guu2020realm": "2002.08909",
    "izacard2023atlas": "2208.03299", "borgeaud2022retro": "2112.04426",
    "gao2023survey": "2312.10997", "asai2024selfrag": "2310.11511",
    "yan2024crag": "2401.15884", "zhao2021calibrate": "2102.09690",
    "shi2023distracted": "2302.00093", "xie2024adaptive": "2305.13300",
    "wang2023sc": "2203.11171", "nogueira2019rerank": "1901.04085",
    "thakur2021beir": "2104.08663", "guo2017calibration": "1706.04599",
    "kandpal2023longtail": "2211.08411", "kadavath2022know": "2207.05221",
    "wang2025conflicting": "2504.13079", "wang2024astute": "2410.07176",
    "ming2024faitheval": "2410.03727",
}
DIRECT_DOIS = {"efron1979": "10.1214/aos/1176344552", "holm1979": "10.2307/4615733",
               "geva2021strategyqa": "10.1162/tacl_a_00370", "khattab2020colbert": "10.1145/3397271.3401075",
               "kbs2024design": "10.1016/j.knosys.2024.112410", "kbs2026trustworthy": "10.1016/j.knosys.2026.116418",
               "wan2024convincing": "10.18653/v1/2024.acl-long.403"}


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "meta" and d.get("name", "").startswith("citation_"):
            self.values.setdefault(d["name"], []).append(d.get("content", ""))


def normalized(text):
    return re.sub(r"[^a-z0-9]", "", re.sub(r"<[^>]*>", "", html.unescape(text)).lower())


def lookup(item):
    key, title = item
    if key in ARXIV:
        target = ROOT / "sources" / "crossref" / f"{key}_arxiv.html"
        try:
            if not target.exists():
                r = requests.get("https://arxiv.org/abs/" + ARXIV[key], timeout=35)
                r.raise_for_status()
                target.write_text(r.text, encoding="utf-8")
            p = MetaParser()
            p.feed(target.read_text(encoding="utf-8"))
            meta = p.values
            found = meta["citation_title"][0]
            score = difflib.SequenceMatcher(None, normalized(title), normalized(found)).ratio()
            return {"key": key, "query": title, "status": "verified" if score >= .99 else "needs_review", "match_score": score,
                    "source": "arxiv", "metadata": {"title": [found], "author": [{"name": n} for n in meta["citation_author"]],
                    "published": {"date-parts": [[int(meta["citation_date"][0][:4])]]}, "type": "posted-content",
                    "DOI": "10.48550/arXiv." + ARXIV[key], "arxiv_id": ARXIV[key]}}
        except (requests.RequestException, KeyError) as e:
            return {"key": key, "query": title, "status": "unresolved", "error": type(e).__name__}
    target = ROOT / "sources" / "crossref" / f"{key}.json"
    if key in DIRECT_DOIS:
        target = target.with_name(key + "_direct.json")
    if target.exists():
        response = json.loads(target.read_text(encoding="utf-8"))
    else:
        response = None
        for attempt in range(3):
            try:
                r = requests.get("https://api.crossref.org/works/" + requests.utils.quote(DIRECT_DOIS[key], safe="") if key in DIRECT_DOIS else "https://api.crossref.org/works", params={} if key in DIRECT_DOIS else {"query.title": title, "rows": 5}, timeout=35)
                r.raise_for_status()
                response = r.json()
                target.write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
                break
            except requests.RequestException:
                time.sleep(attempt + 1)
        if response is None:
            return {"key": key, "query": title, "status": "unresolved"}
    candidates = [response["message"]] if key in DIRECT_DOIS else response["message"]["items"]
    for c in candidates:
        if c.get("subtitle"):
            c["title"] = [c["title"][0] + ": " + c["subtitle"][0]]
    score = lambda x: difflib.SequenceMatcher(None, normalized(title), normalized(x.get("title", [""])[0])).ratio()
    best = max(candidates, key=score)
    return {"key": key, "query": title, "match_score": score(best),
            "status": "verified" if score(best) >= .99 else "needs_review", "metadata": best}


def tex(s):
    s = re.sub("<[^>]*>", "", html.unescape(str(s)))
    s = re.sub(r"\s+", " ", s).strip()
    accents = {"\u0300": "`", "\u0301": "'", "\u0302": "^", "\u0303": "~", "\u0308": '"', "\u030c": "v", "\u0327": "c", "\u030a": "r", "\u0304": "="}
    s = unicodedata.normalize("NFD", s)
    result = []
    for char in s:
        if char in accents and result:
            result[-1] = "\\" + accents[char] + "{" + result[-1] + "}"
        elif ord(char) < 128:
            result.append({"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#"}.get(char, char))
        else:
            result.append({"\u2013": "--", "\u2014": "---", "\u2019": "'", "\u00f8": r"{\o}", "\u0142": r"{\l}", "\u00df": r"{\ss}"}.get(char, char))
    return "".join(result)


def main():
    (ROOT / "sources" / "crossref").mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        rows = list(pool.map(lookup, QUERIES.items()))
    entries = []
    for row in rows:
        if row["status"] != "verified":
            continue
        d = row["metadata"]
        authors = " and ".join(tex(a.get("family", a.get("name", ""))) + (", " + tex(a["given"]) if a.get("given") else "") for a in d.get("author", []))
        date = d.get("published", d.get("issued", {})).get("date-parts", [[None]])[0]
        fields = {"title": "{" + tex(d["title"][0]) + "}", "author": authors,
                  "year": str(date[0]), "doi": d["DOI"]}
        if row["key"] == "brier1950":
            fields["title"] = "{Verification of forecasts expressed in terms of probability}"
            fields["author"] = "Brier, Glenn W."
        if row["key"] == "liang1986gee":
            fields["author"] = "Liang, Kung-Yee and Zeger, Scott L."
        kind = "article" if d["type"] == "journal-article" else "inproceedings"
        container = d.get("container-title", [])
        if container:
            fields["journal" if kind == "article" else "booktitle"] = tex(container[0])
        else:
            kind = "misc"
            fields["howpublished"] = "arXiv preprint arXiv:" + d["arxiv_id"] if d.get("arxiv_id") else "Crossref-indexed preprint"
        for f in ("volume", "issue", "page"):
            if d.get(f):
                fields[{"issue": "number", "page": "pages"}.get(f, f)] = tex(d[f]).replace("-", "--") if f == "page" else tex(d[f])
        entries.append("@" + kind + "{" + row["key"] + ",\n" + ",\n".join("  " + k + " = {" + v + "}" for k, v in fields.items() if v) + "\n}")
    (ROOT / "references.bib").write_text("\n\n".join(entries) + "\n", encoding="utf-8")
    (ROOT / "sources" / "reference_verification.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in rows:
        d = row.get("metadata", {})
        print(row["key"], row["status"], round(row.get("match_score", 0), 3), d.get("title", []), d.get("DOI", ""), flush=True)


if __name__ == "__main__":
    main()
