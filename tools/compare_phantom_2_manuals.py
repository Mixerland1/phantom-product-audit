#!/usr/bin/env python3
"""Compare published Phantom 2 PDF manuals against Word originals.

Requires pdftotext, antiword (for .doc) and Python stdlib.
Comparison is of readable text, NOT a proof of graphical/page identity.
"""
from __future__ import annotations

from collections import Counter
import difflib
import json
import re
import subprocess
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"assets/support/support-phantom-2"
PAIRS=[
  ("Инсталляция Phantom 2.x", "6bb4491d34f9300933eda945df297d27.pdf", "0399aef01f1451bb2228cfbdfb3a51f8.docx"),
  ("Аналоговые пороговые уровни", "eeac0b2b89cb1fc53eece5a2159352d0.pdf", "384e4a645e8111407ae8f06cd31bbbd9.doc"),
  ("Схемы соединений PH_DB25", "8e6ab4ec6eca1c58000a71dab27d983d.pdf", "b7f07fa1b71e344ce390b5c6615c9f38.doc"),
]
W="http://schemas.openxmlformats.org/wordprocessingml/2006/main"

def text_pdf(path:Path)->str:
  p=subprocess.run(["pdftotext","-layout",str(path),"-"],check=True,capture_output=True)
  return p.stdout.decode("utf-8","replace").replace("\f","\n")

def text_word(path:Path)->str:
  if path.suffix==".docx":
    with zipfile.ZipFile(path) as z:
      root=ET.fromstring(z.read("word/document.xml"))
      lines=[]
      for p in root.iter(f"{{{W}}}p"):
        lines.append("".join(n.text or "" for n in p.iter(f"{{{W}}}t")))
      return "\n".join(lines)
  p=subprocess.run(["antiword","-w","0",str(path)],check=True,capture_output=True)
  return p.stdout.decode("utf-8","replace")

def norm(s):
  s=unicodedata.normalize("NFKC",s).casefold().replace("ё","е")
  s=re.sub(r"[^\w]+"," ",s,flags=re.UNICODE)
  return re.sub(r"\s+"," ",s).strip()

def main():
  results=[]
  for label,pdf,word in PAIRS:
    a=text_pdf(DIR/pdf); b=text_word(DIR/word)
    na,nb=norm(a),norm(b)
    ta=na.split();tb=nb.split()
    A,B=Counter(ta),Counter(tb)
    shared=sum((A&B).values())
    precision=shared/max(1,len(tb))
    recall=shared/max(1,len(ta))
    jac=shared/max(1,sum((A|B).values()))
    sim=difflib.SequenceMatcher(None,ta,tb,autojunk=False).ratio() if (len(ta)<50000 and len(tb)<50000) else None
    all_lines_a=[re.sub(r"\s+"," ",x).strip() for x in a.splitlines() if x.strip()]
    all_lines_b=[re.sub(r"\s+"," ",x).strip() for x in b.splitlines() if x.strip()]
    diffs=list(difflib.unified_diff(all_lines_a,all_lines_b,fromfile="pdf",tofile=word,n=1))
    row=dict(label=label,pdf=pdf,word=word,pdf_characters=len(a),word_characters=len(b),pdf_tokens=len(ta),word_tokens=len(tb),
             exact_normalized_match=(na==nb),word_tokens_in_pdf=round(precision,5),pdf_tokens_in_word=round(recall,5),
             token_jaccard=round(jac,5),sequence_similarity=round(sim,5) if sim is not None else None,
             sample_differences=diffs[:80], pdf_text_sample=a[:800],word_text_sample=b[:800])
    results.append(row)
    print("COMPARE",json.dumps({k:v for k,v in row.items() if k not in ("sample_differences","pdf_text_sample","word_text_sample")},ensure_ascii=False),flush=True)
    print("PDF_SAMPLE",repr(a[:320]),flush=True)
    print("WORD_SAMPLE",repr(b[:320]),flush=True)
    print("DIFF_SAMPLE",repr("\n".join(diffs[:28])),flush=True)
  path=ROOT/"docs/phantom-2-word-pdf-comparison.json"
  path.parent.mkdir(parents=True,exist_ok=True)
  path.write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  print("COMPARISON_SAVED",str(path),flush=True)

if __name__=="__main__":
  main()
