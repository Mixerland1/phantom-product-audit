#!/usr/bin/env python3
"""Verify published requisites PDFs without publishing redundant JPEG files.

Each one-page PDF contains the original unmodified JPEG bytes. Check the PDF
and embedded JPEG SHA-256 against the fingerprints recorded when the PDF
copies were generated and visually reviewed. Requires only Python stdlib.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "mdis-ooo-mdis": (
        "04372497b5ba585312f6c5fbd8433dad80c2e5494131d92cdc09c16e09d0e7c0",
        "fdb14b28ea84c6fc255bf830b7d060e9f7f59e5c198c69600948c05f120eb85b",
    ),
    "mdis-information-systems": (
        "23d3a51ea49eb88e823d171a4d6ba9eecc1a11441b7c9a0e90a998fac3addd62",
        "7bb1b5742079d0090245eb0264eba4560fb5c792efbf9c9b15c20f6873dd2615",
    ),
}


def verify_one(name: str, pdf_hash: str, image_hash: str) -> None:
    base = ROOT / "assets" / "requisites"
    pdf = base / (name + ".pdf")
    jpg = base / (name + ".jpg")
    assert pdf.is_file(), f"Missing requisites PDF: {pdf}"
    assert not jpg.exists(), f"Redundant requisites JPG must not be published: {jpg}"
    raw = pdf.read_bytes()
    assert raw.startswith(b"%PDF-1.4\n"), f"Unexpected PDF signature: {pdf}"
    actual_pdf = sha256(raw).hexdigest()
    assert actual_pdf == pdf_hash, f"PDF was modified: {name} {actual_pdf}"
    assert b"/Count 1" in raw, f"Expected single-page PDF: {name}"
    assert raw.count(b"/Subtype /Image") == 1, f"Expected one unmodified source image: {name}"
    start = raw.index(b"/Subtype /Image")
    stream = raw.index(b"stream\n", start) + len(b"stream\n")
    header = raw[start:stream]
    m = re.search(rb"/Length\s+(\d+)", header)
    assert m, f"Cannot locate embedded JPEG length: {name}"
    image = raw[stream:stream + int(m.group(1))]
    assert b"/DCTDecode" in header, f"Image is not embedded as original JPEG: {name}"
    assert image.startswith(b"\xff\xd8") and image.endswith(b"\xff\xd9"), f"Corrupted JPEG stream: {name}"
    actual_jpeg = sha256(image).hexdigest()
    assert actual_jpeg == image_hash, f"Source JPEG bytes in PDF differ: {name} {actual_jpeg}"
    print(f"VERIFIED {pdf.relative_to(ROOT)}: PDF SHA256 {actual_pdf}, "
          f"embedded original JPEG SHA256 {actual_jpeg}", flush=True)


def main() -> None:
    for name, fingerprints in FILES.items():
        verify_one(name, *fingerprints)
    print("PASS: two requisites PDFs, original images embedded byte-for-byte, no separate JPGs", flush=True)


if __name__ == "__main__":
    main()
