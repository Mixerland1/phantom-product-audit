#!/usr/bin/env python3
"""Verify original, non-executed Phantom 2 installer archives and local links."""
from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"assets/support/legacy-media-manifest.json"
EXPECTED={"0d26de81c315bc07de62b5b1554f0c5f.rar",
          "ac503ee2bb08cfee9be9795d499e50fe.rar",
          "b89ccb97df04c6d346f24dbad01c1e02.rar",
          "c41342b68e31dd4d0c5237ac11a60c53.zip"}

def verify():
    rows=json.loads(MANIFEST.read_text(encoding="utf-8"))
    names={r["target"].rsplit("/",1)[-1] for r in rows}
    if len(rows)!=4 or names!=EXPECTED or any(r["kind"]!="archive" for r in rows):
        raise AssertionError("Unexpected legacy archive manifest")
    for row in rows:
        p=ROOT/row["target"]
        if not p.is_file():raise AssertionError(f"Missing archive {p}")
        h=hashlib.sha256()
        with p.open("rb") as f:
            head=f.read(8)
            f.seek(0)
            for chunk in iter(lambda:f.read(1024*1024),b""):
                h.update(chunk)
        if p.stat().st_size!=row["bytes"] or h.hexdigest()!=row["sha256"]:
            raise AssertionError(f"Archive checksum mismatch: {p}")
        if p.suffix==".zip":
            if not head.startswith(b"PK\\x03\\x04"):raise AssertionError(f"Bad ZIP header {p}")
            with zipfile.ZipFile(p) as z:
                if z.testzip() is not None: raise AssertionError(f"Invalid ZIP member {p}")
        elif not head.startswith(b"Rar!\\x1a\\x07"):
            raise AssertionError(f"Bad RAR header {p}")
        html=(ROOT/row["page"]).read_text(encoding="utf-8")
        if row["source"] in html or f'href="{row["target"]}"' not in html:
            raise AssertionError(f"Archive link does not match manifest: {row['page']}")
    print("VERIFIED 4 unmodified archive originals; SHA256, links and ZIP integrity",flush=True)

if __name__=="__main__":
    verify()
