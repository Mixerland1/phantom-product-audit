#!/usr/bin/env python3
"""Browser QA of Phantom integration pages; run from the repository checkout."""
from __future__ import annotations

import json
import os
import re
import threading
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "company.html",
    "news.html",
    "clients.html",
    "partners.html",
    "history.html",
    "rewards.html",
    "articles.html",
    "reviews.html",
    "phantom-active.html",
    "certificates.html",
    "requisites.html",
    "services.html",
    "faq.html",
    "support.html",
    "phantom-home.html",
    "phantom-catalog.html",
    "privacy-policy.html",
]
VIEWPORTS = [(375, 812), (768, 900), (1024, 768), (1440, 900)]
THEMES = ["light", "dark"]
SHOTS = ROOT / "qa-artifacts"
ERRORS: list[str] = []
RESULTS: list[dict] = []


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def require(condition, message: str):
    if not condition:
        raise AssertionError(message)


def inspect_nav(page, filename: str, width: int):
    """Exercise real shared header disclosures and their local routes."""
    require(page.locator(".site-header").count() == 1, "Shared header missing")
    require(page.locator(".footer").count() >= 1, "Footer missing")
    if width > 1080:
        groups = page.locator(".site-nav details.site-menu")
        labels = [group.locator("summary").inner_text().strip() for group in groups.all()]
        require(labels == ["Решения", "Продукты", "Услуги", "Поддержка", "Компания"],
                f"Desktop menu labels: {labels}")
        for label, expected in [
            ("Компания", "certificates.html"),
            ("Услуги", "services.html"),
            ("Поддержка", "faq.html"),
        ]:
            idx = labels.index(label)
            group = groups.nth(idx)
            group.locator("summary").click()
            require(group.get_attribute("open") is not None, f"{label} did not open")
            item = group.locator(f'a[href="{expected}"]')
            if expected == "services.html":
                item = group.locator('.site-menu-all[href="services.html"]')
            require(item.count() == 1 and item.is_visible(), f"{label} missing local route {expected}")
            box = group.locator(".site-menu-panel").bounding_box()
            if box:
                require(box["x"] >= -3 and box["x"] + box["width"] <= width + 3,
                        f"{label} panel outside viewport: {box}")
            group.locator("summary").click()
    else:
        mobile = page.locator(".site-mobile-menu")
        mobile.locator(":scope > summary").click()
        require(mobile.get_attribute("open") is not None, "Mobile menu did not open")
        groups = mobile.locator("details.site-mobile-group")
        labels = [group.locator("summary").inner_text().strip() for group in groups.all()]
        require(labels == ["Решения", "Продукты", "Услуги", "Поддержка", "Компания"],
                f"Mobile menu labels: {labels}")
        for label, route in [
            ("Компания", "certificates.html"),
            ("Услуги", "services.html"),
            ("Поддержка", "faq.html"),
        ]:
            group = groups.nth(labels.index(label))
            group.locator("summary").click()
            require(group.get_attribute("open") is not None, f"Mobile {label} did not open")
            require(group.locator(f'a[href="{route}"]').count() >= 1,
                    f"Mobile {label} missing {route}")
            group.locator("summary").click()
    if filename == "faq.html":
        for anchor in ["general", "versions", "archive", "commercial"]:
            require(page.locator(f"#{anchor}").count() == 1, f"FAQ anchor missing: {anchor}")
    if filename in {"company.html", "clients.html", "certificates.html", "requisites.html", "partners.html", "rewards.html", "history.html"}:
        require(page.locator('.solutions-switcher-label[href="company.html"]').count() == 1,
                "Company cycle link missing")
    if filename == "news.html":
        require(page.locator('a[href="articles.html"]').count() >= 1, "News lack articles link")
        require(page.locator('.solutions-switcher-label[href="#updates"]').count() == 1,
                "News hub context-navigation link missing")
        require(page.locator('a[href="#news-asr"]').count() >= 1,
                "News hub forward navigation missing")
        require(page.locator('a[href="#news-cross"]').count() >= 1,
                "News hub back navigation missing")
        for anchor in ["news-asr", "news-minprom", "news-aviaton", "news-cross"]:
            require(page.locator(f"#{anchor}").count() == 1,
                    f"News article anchor missing: {anchor}")
        require(page.locator('.site-nav a[href="news.html"][aria-current="page"]').count() == 1,
                "News active menu highlight missing")
    if filename == "history.html":
        require(page.locator("nav.history-nav").count() == 0,
                "Obsolete duplicate history navigation remains")
        require(page.locator('a[href="news.html#news-cross"]').count() >= 1,
                "History missing local Cross release")
    if filename == "clients.html":
        require(page.locator('a[href="reviews.html"]').count() >= 1, "Clients lack reviews link")
        require(page.locator('a[href="history.html"]').count() >= 1,
                "Clients missing local company history")
    if filename == "company.html":
        for href in ["clients.html", "partners.html", "history.html"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"Company missing local destination {href}")
    if filename == "partners.html":
        require(page.locator('a[href="company.html"]').count() >= 1,
                "Partners missing company hub")
    if filename == "rewards.html":
        require(page.locator(".rewards-nav").count() == 0, "Obsolete rewards nav remains")
        require(page.locator('a[href^="assets/awards/"][type="application/pdf"]').count() == 5,
                "Five local award documents missing")
    if filename == "reviews.html":
        require(page.locator('.solutions-switcher-label[href="clients.html"]').count() == 1,
                "Reviews child navigation missing")
        require(page.locator('a[href^="assets/reviews/"]').count() == 6,
                "Six local customer letter scans missing")
    if filename == "articles.html":
        require(page.locator('.solutions-switcher-label[href="news.html"]').count() == 1,
                "Articles child navigation missing")
        require(page.locator('a[href="news.html"]').count() >= 1,
                "Articles lack news backlink")
    if filename == "services.html":
        require(page.locator('a[href="personal-solutions.html"]').count() >= 1,
                "Services hub missing personal solutions")
    if filename == "support.html":
        for anchor in ["general", "versions", "archive", "commercial"]:
            require(page.locator(f'a[href="faq.html#{anchor}"]').count() >= 1,
                    f"Support hub missing FAQ route {anchor}")



class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.refs.append((key, attrs[key]))


def check_local_links():
    """Check local HTML/CSS/JS assets and fragment anchors across all root pages."""
    files = sorted(ROOT.glob("*.html"))
    parsed = {}
    for filename in files:
        parser = LinkParser()
        parser.feed(filename.read_text(encoding="utf-8"))
        parsed[filename.resolve()] = parser
    broken = []
    checked = 0
    for file, parser in parsed.items():
        for _kind, ref in parser.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc or ref.startswith("//"):
                continue
            if url.path:
                target = (ROOT / unquote(url.path.lstrip("/"))).resolve() if url.path.startswith("/") else (file.parent / unquote(url.path)).resolve()
            else:
                target = file
            if not target.is_file():
                # Directory-only links can be valid routes when served by a web server.
                if target.is_dir() or (not url.path and not url.fragment):
                    continue
                broken.append(f"{file.name}: missing target {ref}")
                continue
            checked += 1
            if url.fragment and target.suffix.lower() in (".html", ".htm"):
                if target in parsed and unquote(url.fragment) not in parsed[target].ids:
                    broken.append(f"{file.name}: broken anchor {ref}")
    print(f"LINK AUDIT: {len(files)} HTML pages, {checked} local references, {len(broken)} broken", flush=True)
    for item in broken[:100]:
        ERRORS.append(item)
        print("BROKEN LINK", item, flush=True)



def verify_original_assets():
    manifest_path = ROOT / "assets/original-asset-manifest.json"
    require(manifest_path.is_file(), "Original asset manifest not present")
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(len(entries) == 11, f"Expected 11 verified originals, got {len(entries)}")
    import hashlib
    for entry in entries:
        path = ROOT / entry["path"]
        require(path.is_file(), f"Missing original: {entry['path']}")
        data = path.read_bytes()
        magic = b"%PDF-" if path.suffix == ".pdf" else bytes.fromhex("89504e470d0a1a0a")
        require(data.startswith(magic), f"Not a valid original: {path}")
        require(len(data) == entry["bytes"], f"Size mismatch: {path}")
        require(hashlib.sha256(data).hexdigest() == entry["sha256"], f"Hash mismatch: {path}")
    print("ORIGINAL ASSETS: 5 PDF and 6 PNG, signatures and SHA256 verified", flush=True)


def main():
    check_local_links()
    verify_original_assets()
    handler = partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}/"
    SHOTS.mkdir(exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                for width, height in VIEWPORTS:
                    for theme in THEMES:
                        context = browser.new_context(
                            viewport={"width": width, "height": height},
                            device_scale_factor=1,
                            reduced_motion="reduce",
                        )
                        context.add_init_script(f"localStorage.setItem('mdis-theme','{theme}')")
                        page = context.new_page()
                        for filename in PAGES:
                            errors = []
                            page.on("pageerror", lambda error: errors.append(str(error)))
                            ident = f"{filename} {width}px {theme}"
                            try:
                                response = page.goto(base + quote(filename), wait_until="load", timeout=25000)
                                require(response is not None and response.status == 200, "HTML returned non-200")
                                require(page.locator("h1").count() == 1, "Missing or duplicated H1")
                                require(page.locator('meta[name="robots"]').get_attribute("content")
                                        == "noindex, nofollow", "Preview noindex missing")
                                if errors:
                                    raise AssertionError("JavaScript pageerror: " + "; ".join(errors))
                                metrics = page.evaluate("""() => ({
                                    viewport: document.documentElement.clientWidth,
                                    scroll: document.documentElement.scrollWidth,
                                    body: document.body.scrollWidth
                                })""")
                                require(metrics["scroll"] <= metrics["viewport"] + 2
                                        and metrics["body"] <= metrics["viewport"] + 2,
                                        f"Horizontal overflow: {metrics}")
                                broken = page.evaluate("""() => [...document.images]
                                    .filter(i => i.complete && i.naturalWidth === 0 &&
                                       new URL(i.src).origin === location.origin)
                                    .map(i => i.getAttribute('src'))""")
                                require(not broken, f"Broken local images: {broken}")
                                inspect_nav(page, filename, width)
                                RESULTS.append({"page": filename, "width": width, "theme": theme, "ok": True})
                                print("PASS", ident, flush=True)
                            except Exception as error:
                                ERRORS.append(f"{ident}: {error}")
                                print("FAIL", ident, error, flush=True)
                                try:
                                    page.screenshot(path=str(SHOTS / f"{filename}-{width}-{theme}.png"),
                                                    full_page=True, timeout=15000)
                                except Exception:
                                    pass
                        context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
    report = {"passed": len(RESULTS), "failed": len(ERRORS), "errors": ERRORS}
    (SHOTS / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)
    if ERRORS:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
