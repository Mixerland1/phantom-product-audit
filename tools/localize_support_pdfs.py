#!/usr/bin/env python3
"""Copy original MDIS support PDFs into the new site without altering their bytes.

Only PDF hrefs on the five named support child pages are migrated.
Abort without changing tracked files if any source PDF cannot be retrieved
or fails PDF signature/size validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "support-phantom-2.html",
    "support-phantom-4.html",
    "support-phantom-active.html",
    "support-phantom-cross.html",
    "support-stantsiya-zapisi.html",
)
SOURCE_RE = re.compile(r"https://mdis\.ru/upload/iblock/[a-z0-9]+/[a-z0-9]+\.pdf", re.I)
MANIFEST = ROOT / "assets/support/pdf-manifest.json"
MAX_BYTES = 40 * 1024 * 1024
EXPECTED_COUNT = 23


def file_info(data: bytes, name: str) -> dict:
    if len(data) < 1000 or len(data) > MAX_BYTES or not data.startswith(b"%PDF-"):
        raise ValueError(f"Invalid PDF {name}: {len(data)} bytes / {data[:12]!r}")
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def collect() -> tuple[dict[str, str], list[dict]]:
    originals = {}
    items = []
    for page in PAGES:
        html = (ROOT / page).read_text(encoding="utf-8")
        originals[page] = html
        for url in sorted(set(SOURCE_RE.findall(html))):
            name = Path(urlsplit(url).path).name
            dest = f"assets/support/{Path(page).stem}/{name}"
            items.append({"page": page, "source": url, "path": dest})
    if len(items) != EXPECTED_COUNT or len(set(x["path"] for x in items)) != EXPECTED_COUNT:
        raise ValueError(f"Expected {EXPECTED_COUNT} unique PDF links; found {len(items)}")
    return originals, items


def download(item: dict, folder: Path) -> tuple[dict, bytes]:
    file_path = ROOT / item["path"]
    if file_path.exists():
        data = file_path.read_bytes()
    else:
        temporary = folder / Path(item["path"]).name
        subprocess.run(
            [
                "curl", "--fail", "--location", "--silent", "--show-error",
                "--retry", "2", "--connect-timeout", "15", "--max-time", "100",
                "--max-filesize", str(MAX_BYTES),
                "--user-agent", "Mozilla/5.0 (compatible; MDIS-asset-import/1.0)",
                "--output", str(temporary), item["source"],
            ],
            check=True,
            timeout=310,
        )
        data = temporary.read_bytes()
    file_info(data, item["source"])
    return item, data


def verify() -> None:
    rows = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if len(rows) != EXPECTED_COUNT:
        raise ValueError(f"Wrong manifest count: {len(rows)}")
    for row in rows:
        data = (ROOT / row["path"]).read_bytes()
        if file_info(data, row["path"]) != {
            "bytes": row["bytes"], "sha256": row["sha256"]
        }:
            raise ValueError(f"PDF checksum mismatch: {row['path']}")
        html = (ROOT / row["page"]).read_text(encoding="utf-8")
        if row["source"] in html or f'href="{row["path"]}"' not in html:
            raise ValueError(f"Unmigrated URL: {row['page']}, {row['source']}")
    print(f"VERIFIED {len(rows)} local original PDFs, SHA-256 and page links")


def migrate() -> None:
    originals, items = collect()
    payloads = {}
    with tempfile.TemporaryDirectory(prefix="phantom-pdfs-") as td:
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(download, x, Path(td)) for x in items]
            for future in as_completed(futures):
                item, data = future.result()
                payloads[item["path"]] = data
                info = file_info(data, item["path"])
                print(f"FETCHED {item['page']} {Path(item['path']).name} {info['bytes']} bytes", flush=True)
    # All downloads passed before the first write.
    manifest = []
    updated = dict(originals)
    for item in sorted(items, key=lambda x: (x["page"], x["path"])):
        path = ROOT / item["path"]
        data = payloads[item["path"]]
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f"Refusing to overwrite changed binary: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        manifest.append({**item, **file_info(data, item["path"])})
        updated[item["page"]] = updated[item["page"]].replace(item["source"], item["path"])
    for page, text in updated.items():
        if SOURCE_RE.search(text):
            raise ValueError(f"Unmigrated PDF link in {page}")
        (ROOT / page).write_text(text, encoding="utf-8")
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    verify()
    print(f"MIGRATED {len(manifest)} PDFs on {len(PAGES)} pages")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    verify() if args.verify else migrate()
