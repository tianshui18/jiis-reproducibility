"""Compile the supplied CAS template and render every final PDF page for QA."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import fitz
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
OUTPUT = ROOT / "output" / "pdf"
QA = ROOT / "qa"


def run(args, cwd, env, logname):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    (BUILD/logname).write_text(result.stdout+"\n"+result.stderr,encoding="utf-8")
    if result.returncode:
        print((result.stdout+result.stderr)[-6000:])
        raise RuntimeError(f"Command failed ({result.returncode}): {args}")
    return result.stdout


def main():
    for p in (BUILD,OUTPUT,QA): p.mkdir(parents=True,exist_ok=True)
    template=ROOT.parent/"template"/"els-cas-templates"
    for name in ("cas-sc.cls","cas-dc.cls","cas-common.sty","cas-model2-names.bst"):
        if not (ROOT/name).exists(): shutil.copy2(template/name,ROOT/name)
    if not (ROOT/"elsarticle-num.bst").exists():
        found=subprocess.run(["kpsewhich","elsarticle-num.bst"],capture_output=True,text=True,check=True).stdout.strip()
        shutil.copy2(found,ROOT/"elsarticle-num.bst")
    env=dict(os.environ)
    for name in ("TEXINPUTS","BIBINPUTS","BSTINPUTS"):
        env[name]=str(ROOT)+os.pathsep+env.get(name,"")
    versions={}
    for tool in ("pdflatex","bibtex","pdftoppm"):
        path=shutil.which(tool)
        if not path: raise RuntimeError(f"Required command missing: {tool}")
        versions[tool]=path
    tool_versions={}
    for tool,path in versions.items():
        flag="-v" if tool=="pdftoppm" else "--version"
        result=subprocess.run([path,flag],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=30)
        tool_versions[tool]=(result.stdout+result.stderr).strip()
    reports={}
    for source,dest in (("main","manuscript"),("supplement","supplement")):
        # Remove render products from earlier page counts before producing QA sheets.
        for stale in QA.glob(dest + "-*.png"):
            stale.unlink()
        for stale in QA.glob(dest + "_contact_*.png"):
            stale.unlink()
        cmd=[versions["pdflatex"],"-interaction=nonstopmode","-halt-on-error","-file-line-error","-output-directory=build",source+".tex"]
        run(cmd,ROOT,env,source+"_pass1.txt")
        if source=="main": run([versions["bibtex"],"main"],BUILD,env,"main_bibtex.txt")
        for n in (2,3): run(cmd,ROOT,env,source+f"_pass{n}.txt")
        # Long float sequences can need additional passes after a clean checkout.
        for n in range(4, 9):
            current_log=(BUILD/(source+".log")).read_text(encoding="utf-8",errors="replace")
            if not re.search(r"Rerun to get|Label\(s\) may have changed|Please rerun LaTeX",current_log,re.I):
                break
            run(cmd,ROOT,env,source+f"_pass{n}.txt")
        current_log=(BUILD/(source+".log")).read_text(encoding="utf-8",errors="replace")
        if re.search(r"Rerun to get|Label\(s\) may have changed|Please rerun LaTeX",current_log,re.I):
            raise RuntimeError(f"Cross-references failed to converge after eight passes: {source}")
        target=OUTPUT/(dest+".pdf")
        shutil.copy2(BUILD/(source+".pdf"),target)
        log=(BUILD/(source+".log")).read_text(encoding="utf-8",errors="replace")
        warnings=[line for line in log.splitlines() if re.search(r"warning\s*:|Overfull", line, re.I)]
        doc=fitz.open(target)
        prefix=QA/dest
        run([versions["pdftoppm"],"-r","85","-png",str(target),str(prefix)],ROOT,env,source+"_render.txt")
        pages=[]
        outside=[]
        for i,page in enumerate(doc):
            text=page.get_text()
            pages.append({"page":i+1,"text_characters":len(text),"images":len(page.get_images()),"size":[page.rect.width,page.rect.height]})
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block: continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        x0,y0,x1,y1=span["bbox"]
                        if x0 < -1 or y0 < -1 or x1 > page.rect.width+1 or y1>page.rect.height+1:
                            outside.append({"page":i+1,"text":span["text"],"bbox":span["bbox"]})
        for offset in range(0,len(doc),6):
            montage=Image.new("RGB",(3*460,2*675),"#DDDDDD")
            draw=ImageDraw.Draw(montage)
            for i in range(offset,min(offset+6,len(doc))):
                matches=list(QA.glob(f"{dest}-{i+1:0{len(str(len(doc)))}d}.png"))
                if not matches: matches=list(QA.glob(f"{dest}-{i+1}.png"))
                im=Image.open(matches[0]).convert("RGB"); im.thumbnail((440,625))
                j=i-offset; x=(j%3)*460+(460-im.width)//2; y=(j//3)*675+27
                montage.paste(im,(x,y)); draw.text(((j%3)*460+15,(j//3)*675+7),f"{dest}: page {i+1}",fill="black")
            montage.save(QA/f"{dest}_contact_{offset//6+1}.png")
        reports[source]={"pdf":str(target),"pages":pages,"warnings":warnings,"outside_page_text":outside}
        print(source,len(doc),"pages;",len(warnings),"warnings;",len(outside),"text spans outside page",flush=True)
    report={"tools":versions,"tool_versions":tool_versions,"pdfs":reports}
    (QA/"compile_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")


if __name__=="__main__": main()
