#!/usr/bin/env python3
"""Localize all remaining official Word documents from MDIS support child pages.

Preserve original bytes; validate file signatures, DOCX internal structure, SHA-256,
the final HTML hrefs and exact count. Never migrate EXE/RAR/ZIP/MP4.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import subprocess
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "support-phantom-2.html",
    "support-phantom-4.html",
    "support-phantom-active.html",
    "support-phantom-ultra.html",
)
SOURCE_RE = re.compile(r'https://mdis\.ru/upload/iblock/[a-z0-9]+/[a-z0-9]+\.(?:docx|doc)(?=["\'])', re.I)
MANIFEST = ROOT / "assets/support/word-manifest.json"
EXPECTED_COUNT = 17
MAX_BYTES = 40 * 1024 * 1024
OLE_MAGIC = bytes.fromhex("d0cf11e0a1b11ae1")


def validated(data: bytes, path: str) -> dict:
    ext = Path(path).suffix.lower()
    if not (100 <= len(data) <= MAX_BYTES):
        raise ValueError(f"Unexpected Word document size {path}: {len(data)}")
    if ext == ".docx":
        if not zipfile.is_zipfile(io.BytesIO(data)):
            raise ValueError(f"Invalid ZIP container for DOCX: {path}")
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = set(zf.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise ValueError(f"DOCX lacks required Word parts: {path}")
    elif ext == ".doc":
        if not (data.startswith(OLE_MAGIC) or data[:20].lstrip().startswith(b"{\\rtf")):
            raise ValueError(f"Not OLE DOC or RTF document: {path}; header={data[:20]!r}")
    else:
        raise ValueError(f"Unsupported extension: {path}")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def discover():
    original = {}
    rows = []
    for page in PAGES:
        html = (ROOT / page).read_text(encoding="utf-8")
        original[page] = html
        for url in sorted(set(SOURCE_RE.findall(html))):
            name = url.rsplit("/", 1)[-1]
            path = f"assets/support/{Path(page).stem}/{name}"
            rows.append({"page": page, "source": url, "path": path})
    if len(rows) != EXPECTED_COUNT or len({r["path"] for r in rows}) != EXPECTED_COUNT:
        raise ValueError(f"Expected {EXPECTED_COUNT} unique DOC/DOCX, found {len(rows)}")
    return original, rows


def get(item: dict, temporary_dir: Path):
    path = ROOT / item["path"]
    if path.exists():
        data = path.read_bytes()
    else:
        out = temporary_dir / Path(item["path"]).name
        subprocess.run(
            ["curl", "--fail", "--location", "--silent", "--show-error",
             "--retry", "2", "--connect-timeout", "15", "--max-time", "95",
             "--max-filesize", str(MAX_BYTES), "--user-agent", "Mozilla/5.0",
             "--output", str(out), item["source"]],
            check=True, timeout=320
        )
        data = out.read_bytes()
    return item, data, validated(data, item["path"])


def verify():
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if len(rows) != EXPECTED_COUNT:
        raise ValueError(f"Wrong manifest count: {len(rows)}")
    for row in rows:
        data = (ROOT / row["path"]).read_bytes()
        actual = validated(data, row["path"])
        if actual != {key: row[key] for key in ("bytes", "sha256")}:
            raise ValueError(f"Checksum mismatch: {row['path']}")
        html = (ROOT / row["page"]).read_text(encoding="utf-8")
        if row["source"] in html or f'href="{row["path"]}"' not in html:
            raise ValueError(f"Link mismatch: {row['page']} {row['path']}")
    print(f"VERIFIED {len(rows)} original DOC/DOCX files and local HTML links", flush=True)


def migrate():
    original, rows = discover()
    data_by_path = {}
    metadata_by_path = {}
    with tempfile.TemporaryDirectory(prefix="phantom-word-") as temp:
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = [pool.submit(get, row, Path(temp)) for row in rows]
            for future in as_completed(futures):
                row, data, meta = future.result()
                data_by_path[row["path"]] = data
                metadata_by_path[row["path"]] = meta
                print(f"FETCHED {row['page']} {Path(row['path']).name} {meta['bytes']} bytes", flush=True)
    # Download/validation must complete before tracked-file modifications.
    updated = dict(original)
    manifest = []
    for row in sorted(rows, key=lambda r: (r["page"], r["path"])):
        path = ROOT / row["path"]
        data = data_by_path[row["path"]]
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"Refusing to overwrite changed original: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        updated[row["page"]] = updated[row["page"]].replace(row["source"], row["path"])
        manifest.append({**row, **metadata_by_path[row["path"]]})
    for page, html in updated.items():
        if SOURCE_RE.search(html):
            raise ValueError(f"External Word documents remain on {page}")
        (ROOT / page).write_text(html, encoding="utf-8")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verify()
    print(f"MIGRATED {len(manifest)} Word documents on {len(PAGES)} pages")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    verify() if args.verify else migrate()
