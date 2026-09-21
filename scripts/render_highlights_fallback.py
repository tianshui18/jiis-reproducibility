"""Independent DOCX rendering fallback when local Office export is unavailable."""
from pathlib import Path
import subprocess
from spire.doc import Document, FileFormat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa/highlights"
OUT.mkdir(parents=True, exist_ok=True)
doc = Document()
doc.LoadFromFile(str(ROOT / "highlights.docx"))
pdf = OUT / "highlights_spire.pdf"
doc.SaveToFile(str(pdf), FileFormat.PDF)
doc.Close()
subprocess.run(["pdftoppm", "-r", "120", "-png", str(pdf), str(OUT / "spire")], check=True)
print(pdf)
