#!/usr/bin/env python3
"""Wrap the two *unaltered* official JPEG requisites scans into PDFs.

No OCR, retouching, rewriting or JPEG re-encoding. Original JPEG byte streams
are placed as PDF DCTDecode XObjects; original JPGs remain available.
Use --check in CI to compare generated PDFs byte-for-byte.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets" / "requisites"
FILES = ["mdis-ooo-mdis", "mdis-information-systems"]
SOF_MARKERS = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def jpeg_properties(data: bytes) -> tuple[int, int, int]:
    """Read dimensions and component count from JPEG SOF; no raster decode."""
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("Not a JPEG file")
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            raise ValueError(f"Invalid JPEG marker offset {i}")
        while data[i] == 0xFF:
            i += 1
        marker = data[i]
        i += 1
        if marker in (0xD9, 0xDA):
            break
        if marker in (0x01, *range(0xD0, 0xD8)):
            continue
        if i + 2 > len(data):
            break
        length = int.from_bytes(data[i : i + 2], "big")
        if length < 2 or i + length > len(data):
            raise ValueError("Invalid JPEG segment length")
        if marker in SOF_MARKERS:
            if length < 8:
                raise ValueError("Invalid JPEG SOF")
            precision = data[i + 2]
            height = int.from_bytes(data[i + 3 : i + 5], "big")
            width = int.from_bytes(data[i + 5 : i + 7], "big")
            components = data[i + 7]
            if precision != 8 or min(width, height) < 1 or components not in (1, 3):
                raise ValueError(f"Unsupported JPEG: {width}x{height}, {precision}-bit, {components} components")
            return width, height, components
        i += length
    raise ValueError("Cannot determine JPEG dimensions")


def pdf_from_jpeg(jpeg: bytes, title: str) -> bytes:
    width, height, components = jpeg_properties(jpeg)
    # A4 with natural image orientation; 24 pt margins, no crop or stretch.
    page_w, page_h = (595.276, 841.89) if height >= width else (841.89, 595.276)
    margin = 24.0
    scale = min((page_w - 2 * margin) / width, (page_h - 2 * margin) / height)
    dw, dh = width * scale, height * scale
    x, y = (page_w - dw) / 2, (page_h - dh) / 2
    drawing = f"q\n{dw:.4f} 0 0 {dh:.4f} {x:.4f} {y:.4f} cm\n/Im1 Do\nQ\n".encode("ascii")
    cs = "/DeviceRGB" if components == 3 else "/DeviceGray"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w:.3f} {page_h:.3f}] "
         "/Resources << /XObject << /Im1 5 0 R >> >> /Contents 4 0 R >>").encode("ascii"),
        f"<< /Length {len(drawing)} >>\nstream\n".encode("ascii") + drawing + b"endstream",
        (f"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} /ColorSpace {cs} "
         f"/BitsPerComponent 8 /Filter /DCTDecode /Length {len(jpeg)} >>\nstream\n").encode("ascii")
        + jpeg + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, payload in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("ascii"))
        pdf.extend(payload)
        pdf.extend(b"\nendobj\n")
    cross_ref = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("ascii"))
    for pos in offsets[1:]:
        pdf.extend(f"{pos:010d} 00000 n \n".encode("ascii"))
    pdf.extend((f"trailer\n<< /Root 1 0 R /Size {len(offsets)} >>\n"
                f"startxref\n{cross_ref}\n%%EOF\n").encode("ascii"))
    # The source image bytes must be present in the resulting PDF unchanged.
    assert bytes(pdf).count(jpeg) == 1
    return bytes(pdf)


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--check", action="store_true", help="Read-only: check two existing PDFs match source scans exactly")
    args = cli.parse_args()
    for name in FILES:
        source = ASSET_DIR / (name + ".jpg")
        output = ASSET_DIR / (name + ".pdf")
        jpeg = source.read_bytes()
        data = pdf_from_jpeg(jpeg, name)
        props = jpeg_properties(jpeg)
        if args.check:
            if not output.is_file() or output.read_bytes() != data:
                raise SystemExit(f"FAIL: PDF missing or does not contain the original JPEG unchanged: {output}")
            status = "VERIFIED"
        else:
            output.write_bytes(data)
            status = "CREATED"
        print(f"{status} {output.relative_to(ROOT)} — JPG {props[0]}x{props[1]}, "
              f"source SHA256 {hashlib.sha256(jpeg).hexdigest()}, "
              f"PDF SHA256 {hashlib.sha256(data).hexdigest()}, {len(data)} bytes")
    print("OK: both PDFs are faithful one-page wrappers around original JPEG bytes")


if __name__ == "__main__":
    main()
