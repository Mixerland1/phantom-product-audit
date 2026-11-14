#!/usr/bin/env python3
"""Browser QA of Phantom integration pages; run from the repository checkout."""
from __future__ import annotations

import json
import os
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "company.html",
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
    if filename in {"company.html", "certificates.html", "requisites.html"}:
        require(page.locator('.solutions-switcher-label[href="company.html"]').count() == 1,
                "Company cycle link missing")
    if filename == "services.html":
        require(page.locator('a[href="personal-solutions.html"]').count() >= 1,
                "Services hub missing personal solutions")
    if filename == "support.html":
        for anchor in ["general", "versions", "archive", "commercial"]:
            require(page.locator(f'a[href="faq.html#{anchor}"]').count() >= 1,
                    f"Support hub missing FAQ route {anchor}")


def main():
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
