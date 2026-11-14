#!/usr/bin/env python3
"""Browser QA of Phantom integration pages; run from the repository checkout."""
from __future__ import annotations

import hashlib
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
    "atom-energy.html",
    "stantsiya-zapisi.html",
    "industrial.html",
    "government.html",
    "commercial.html",
    # Audit 05 and the previously uncovered pages from audits 07–12.
    # Phantom Active and the catalog are already listed above.
    "financial.html",
    "auto-dealers.html",
    "phantom-micro.html",
    "phantom-boards.html",
    "ip-telephony.html",
    # Audited pages 13–18: one real Chromium case per width and theme.
    "connection-schemes.html",
    "personal-solutions.html",
    "modernization.html",
    "training.html",
    "telephone-recording.html",
    "dispatcher-recording.html",
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


def assert_theme(page, expected: str):
    actual = page.locator("html").get_attribute("data-theme")
    require(actual == expected, f"Theme mismatch: expected {expected}, got {actual}")
    pressed = page.locator(".site-theme-toggle").get_attribute("aria-pressed")
    require(pressed == str(expected == "dark").lower(),
            f"Theme toggle state mismatch: {pressed}")


def inspect_theme_persistence(page, base: str, initial: str):
    """Exercise real theme-toggle clicks, styling, navigation, and reload."""
    opposite = "dark" if initial == "light" else "light"
    original_paper = page.evaluate(
        "() => getComputedStyle(document.documentElement).getPropertyValue('--paper').trim()")
    page.locator(".site-theme-toggle").click()
    assert_theme(page, opposite)
    require(page.evaluate("() => localStorage.getItem('mdis-theme')") == opposite,
            "Theme choice not saved")
    changed_paper = page.evaluate(
        "() => getComputedStyle(document.documentElement).getPropertyValue('--paper').trim()")
    require(original_paper != changed_paper, "Theme did not change page styling")
    response = page.goto(base + "commercial.html", wait_until="load", timeout=25000)
    require(response is not None and response.status == 200,
            "Theme navigation target unavailable")
    assert_theme(page, opposite)
    require(page.evaluate("() => localStorage.getItem('mdis-theme')") == opposite,
            "Theme lost on navigation")
    page.reload(wait_until="load", timeout=25000)
    assert_theme(page, opposite)
    page.locator(".site-theme-toggle").click()
    assert_theme(page, initial)
    require(page.evaluate("() => localStorage.getItem('mdis-theme')") == initial,
            "Theme not restored after toggling back")
    response = page.goto(base + "company.html", wait_until="load", timeout=25000)
    require(response is not None and response.status == 200,
            "Could not return to company page")
    assert_theme(page, initial)


def inspect_nav(page, filename: str, width: int):
    """Exercise real shared header disclosures and their local routes."""
    require(page.locator(".site-header").count() == 1, "Shared header missing")
    require(page.locator(".footer").count() >= 1, "Footer missing")
    require(page.locator('.footer-logos a[href="company.html"]').count() == 1,
            "MDIS footer logo must link to local company page")
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
        products = groups.nth(labels.index("Продукты"))
        products.locator("summary").click()
        featured = products.locator('.site-menu-list > a.site-menu-card--featured[href="connection-schemes.html"]')
        require(featured.count() == 1 and featured.is_visible(),
                "Featured connection schemes missing from desktop Products menu")
        require(products.locator(".site-menu-list > a").first.get_attribute("href")
                == "connection-schemes.html", "Schemes are not first in Products menu")
        products.locator("summary").click()
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
            ("Продукты", "connection-schemes.html"),
        ]:
            group = groups.nth(labels.index(label))
            group.locator("summary").click()
            require(group.get_attribute("open") is not None, f"Mobile {label} did not open")
            require(group.locator(f'a[href="{route}"]').count() >= 1,
                    f"Mobile {label} missing {route}")
            if label == "Продукты":
                featured = group.locator('.site-menu-card--featured[href="connection-schemes.html"]')
                require(featured.count() == 1 and featured.is_visible(),
                        "Featured connection schemes missing from mobile Products menu")
                require(group.locator(".site-menu-card").first.get_attribute("href")
                        == "connection-schemes.html", "Schemes are not first on mobile")
            group.locator("summary").click()
    if filename == "phantom-home.html" and width in (375, 1440):
        if width > 1080:
            menu = page.locator(".site-nav .site-menu").nth(1)
        else:
            menu = page.locator(".site-mobile-menu .site-mobile-group").nth(1)
        menu.locator("summary").click()
        menu.locator('a.site-menu-card--featured[href="connection-schemes.html"]').click()
        page.wait_for_url("**/connection-schemes.html", timeout=15000)
        require("Схемы подключения" in page.locator("h1").inner_text(),
                "Featured menu link opened the wrong page")
        page.go_back(wait_until="load", timeout=15000)
        require(page.url.endswith("/phantom-home.html"),
                "Home page was not restored after featured menu navigation")
    if filename == "financial.html":
        for href in ["index.html", "news.html#news-minprom",
                     "phantom-pro-level-5.html", "phantom-pro-level-6.html"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"Financial page missing local route {href}")
        require(page.locator(".demo").count() == 0,
                "Financial page still shows a draft notice")
    if filename == "auto-dealers.html":
        for href in ["clients.html#sector-6", "phantom-asr.html"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"Autodealers page missing local route {href}")
        require(page.locator(".demo").count() == 0,
                "Autodealers still shows a draft notice")
    if filename == "phantom-micro.html":
        require(page.locator('img[src="assets/products/phantom-micro-hero.webp"]').count() == 1,
                "MICRO product image missing")
        require(page.locator('a[href="phantom-catalog.html"]').count() >= 1,
                "MICRO missing catalog backlink")
        require(page.locator(".micro-spec").count() == 1,
                "MICRO technical specifications missing")
    if filename == "phantom-boards.html":
        for asset in ["phantom-ph-200.jpg", "phantom-ph-500.png", "phantom-ph-600.jpg"]:
            require(page.locator(f'img[src="assets/products/{asset}"]').count() == 1,
                    f"Individual Phantom board image missing: {asset}")
        for href in ["support-phantom-2.html", "support-phantom-4.html"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"Boards missing documentation route {href}")
    if filename == "phantom-active.html":
        for href in ["support-phantom-active.html#manuals",
                     "support-phantom-active.html#integrations",
                     "support-phantom-active.html#brochures", "training.html"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"Phantom Active missing local route {href}")
    if filename == "ip-telephony.html":
        for href in ["phantom-active.html", "phantom-monitoring.html",
                     "connection-schemes.html"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"IP telephony missing local route {href}")
        require(page.locator('a[href^="https://mdis.ru/"]').count() == 0,
                "IP telephony links to old MDIS site")
    if filename == "phantom-catalog.html":
        require(page.locator(".product-card .product-image img").count() == 5,
                "Catalog must show five individual model images")
        for href in ["phantom-micro.html", "phantom-pc-2.html",
                     "phantom-pro-level-5.html", "phantom-pro-level-6.html",
                     "phantom-ultra.html"]:
            require(page.locator(f'.product-image[href="{href}"]').count() == 1,
                    f"Catalog model card missing route {href}")
    if filename == "connection-schemes.html":
        expected = ["ip-principle", "tricom", "minicom", "protocols"]
        for anchor in expected:
            require(page.locator(f"#{anchor}").count() == 1,
                    f"Missing original connection scheme section: {anchor}")
        for img in ["ip-principle.webp", "tricom-gip.webp",
                    "minicom-dx500.webp", "protocols-sip-h323.webp"]:
            require(page.locator(f'img[src="assets/schemes/{img}"]').count() == 1,
                    f"Connection scheme image missing: {img}")
        require(page.locator("a[href^='https://mdis.ru/']").count() == 0,
                "Connection schemes link to legacy site")
    if filename in {"personal-solutions.html", "modernization.html", "training.html"}:
        require(page.locator('.solutions-switcher-label[href="services.html"]').count() == 1,
                "Service hub link missing")
        require(page.locator(".solutions-switcher").count() == 1,
                "Duplicate or missing service navigation")
    if filename == "personal-solutions.html":
        require(page.locator('.solutions-switcher-neighbor--previous[href="training.html"]').count() == 1,
                "Service cycle should wrap from personal solutions to training")
        require(page.locator('.solutions-switcher-neighbor--next[href="modernization.html"]').count() == 1,
                "Personal solutions next link incorrect")
    if filename == "modernization.html":
        require(page.locator('.solutions-switcher-neighbor--previous[href="personal-solutions.html"]').count() == 1,
                "Modernization previous link incorrect")
        require(page.locator('.solutions-switcher-neighbor--next[href="training.html"]').count() == 1,
                "Modernization next link incorrect")
        require(page.locator('a[href="history.html#modernization"]').count() >= 1,
                "Modernization case should link to local history")
    if filename == "training.html":
        require(page.locator('.solutions-switcher-neighbor--previous[href="modernization.html"]').count() == 1,
                "Training previous neighbour incorrect")
        require(page.locator('.solutions-switcher-neighbor--next[href="personal-solutions.html"]').count() == 1,
                "Training next neighbour must be personal solutions, not the hub")
        require(page.locator('a[href="connection-schemes.html"]').count() >= 1,
                "Training page lacks connection schemes")
        if width == 375:
            page.locator(".solutions-switcher-control").last.click()
            page.wait_for_url("**/personal-solutions.html", timeout=15000)
            page.go_back(wait_until="load", timeout=15000)
            require(page.url.endswith("/training.html"),
                    "Service next arrow did not navigate and return correctly")
    if filename == "telephone-recording.html":
        for href in ["phantom-boards.html", "connection-schemes.html",
                     "phantom-catalog.html#telephone-recording"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"Telephone-recording local route missing: {href}")
    if filename == "dispatcher-recording.html":
        for href in ["attestation-fsk-ees.html", "telephone-recording.html",
                     "connection-schemes.html"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"Dispatcher-recording local route missing: {href}")
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
    if filename == "requisites.html":
        downloads = [
            ("assets/requisites/mdis-ooo-mdis.jpg", "Реквизиты_ООО_МДИС.jpg",
             "fdb14b28ea84c6fc255bf830b7d060e9f7f59e5c198c69600948c05f120eb85b"),
            ("assets/requisites/mdis-information-systems.jpg",
             "Реквизиты_ООО_МД_Информационные_Системы.jpg",
             "7bb1b5742079d0090245eb0264eba4560fb5c792efbf9c9b15c20f6873dd2615"),
        ]
        for href, name, checksum in downloads:
            link = page.locator(f'.doc-card a.open-link[href="{href}"][download="{name}"]')
            require(link.count() == 1, f"Local requisites download missing: {href}")
            if width == 375:
                with page.expect_download(timeout=15000) as download_event:
                    link.click()
                saved = download_event.value
                require(saved.suggested_filename == name,
                        f"Unexpected download filename: {saved.suggested_filename}")
                actual = hashlib.sha256(Path(saved.path()).read_bytes()).hexdigest()
                require(actual == checksum, f"Downloaded requisites JPG checksum mismatch: {href}")
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
    pdfs = [e for e in entries if e['path'].endswith('.pdf')]
    pngs = [e for e in entries if e['path'].endswith('.png')]
    require(len(pdfs) == 5 and len(pngs) == 6,
            f'Expected 5 award PDFs and 6 letter PNGs; got {len(pdfs)}, {len(pngs)}')
    require(len({e['path'] for e in entries}) == 11,
            'Duplicate original asset manifest paths')
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
    require(len(PAGES) == len(set(PAGES)),
            "Duplicate HTML pages in browser QA matrix")
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
                        context.add_init_script(f"""if (!localStorage.getItem('mdis-theme')) {{
                            localStorage.setItem('mdis-theme','{theme}');
                        }}""")
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
                                assert_theme(page, theme)
                                inspect_nav(page, filename, width)
                                if filename == "company.html":
                                    inspect_theme_persistence(page, base, theme)
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
