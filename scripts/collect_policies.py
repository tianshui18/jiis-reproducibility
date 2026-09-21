"""Archive accessible official guidance and record inaccessible URLs honestly."""
import json
from html.parser import HTMLParser
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]/"sources"


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip=0; self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style"): self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style"): self.skip=max(0,self.skip-1)
        if tag in ("p","li","h1","h2","h3","h4"): self.parts.append("\n")
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)


def main():
    urls={"kbs_guide":"https://www.sciencedirect.com/journal/knowledge-based-systems/publish/guide-for-authors",
          "elsevier_ai_policy":"https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals",
          "elsevier_highlights":"https://www.elsevier.com/researcher/author/tools-and-resources/highlights",
          "elsevier_artwork":"https://www.elsevier.com/researcher/author/policies-and-guidelines/artwork-and-media-instructions"}
    results={}
    for name,url in urls.items():
        try:
            r=requests.get(url,timeout=25)
            results[name]={"requested_url":url,"resolved_url":r.url,"http_status":r.status_code,"accessed":"2026-09-18"}
            if r.ok:
                (ROOT/(name+".html")).write_text(r.text,encoding="utf-8")
                p=Text(); p.feed(r.text)
                text=" ".join(p.parts)
                (ROOT/(name+".txt")).write_text(text,encoding="utf-8")
                results[name]["text_characters"]=len(text)
        except requests.RequestException as e:
            results[name]={"requested_url":url,"error":type(e).__name__}
    (ROOT/"policy_access.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    print(json.dumps(results,indent=2))


if __name__=="__main__": main()
