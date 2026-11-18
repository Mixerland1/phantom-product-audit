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
from verify_legacy_archives import verify as verify_legacy_archives

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
    "contacts.html",
    "services.html",
    "faq.html",
    "support.html",
    "support-phantom-2.html",
    "support-phantom-4.html",
    "support-phantom-active.html",
    "support-phantom-cross.html",
    "support-phantom-ultra.html",
    "support-stantsiya-zapisi.html",
    "phantom-home.html",
    "solutions.html",
    "phantom-catalog.html",
    "privacy-policy.html",
    "cookie-policy.html",
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
    # Audited pages 19–23; support, financial, IP and telephone are already covered.
    "pultex.html",
    "phantom-cross.html",
    "phantom-monitoring.html",
    "phantom-asr.html",
    "selective-recording.html",
    # Final prompt 46: full canonical site, including original CRM and model pages.
    "attestation-fsk-ees.html",
    "aviation-transport.html",
    "aviaton.html",
    "electroenergetika.html",
    "index.html",
    "phantom-pc-2.html",
    "phantom-pro-level-5.html",
    "phantom-pro-level-6.html",
    "phantom-ultra.html",
    "migration-progress.html",
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


def inspect_active_underline_hover(page, filename: str, width: int):
    """The current top-level nav underline yields to a different hovered item."""
    if width != 1440 or filename not in {
        "connection-schemes.html", "atom-energy.html", "training.html",
        "company.html", "faq.html", "news.html",
    }:
        return
    if filename == "news.html":
        active = page.locator('.site-nav > a[href="news.html"][aria-current="page"]')
        other = page.locator(".site-nav > details.site-menu").nth(1).locator("summary")
    else:
        active = page.locator(".site-nav > details.site-menu--current > summary")
        other = page.locator('.site-nav > a[href="news.html"]')
    require(active.count() == 1 and other.count() == 1,
            f"Active/other nav items not resolved on {filename}")

    def underline_opacity():
        return float(active.evaluate(
            "(node) => getComputedStyle(node, '::after').opacity"))

    page.mouse.move(2, 500)
    page.wait_for_timeout(260)
    require(underline_opacity() > 0.95,
            "Current nav underline missing with pointer away")
    active.hover()
    page.wait_for_timeout(260)
    require(underline_opacity() > 0.95,
            "Current nav underline should stay while hovering its own item")
    other.hover()
    page.wait_for_timeout(260)
    require(underline_opacity() < 0.05,
            "Current nav underline remains visible while another nav item is hovered")
    page.mouse.move(2, 500)
    page.wait_for_timeout(260)
    require(underline_opacity() > 0.95,
            "Current nav underline did not return after pointer left navigation")


def inspect_nav(page, filename: str, width: int):
    """Exercise real shared header disclosures and their local routes."""
    require(page.locator(".site-header").count() == 1, "Shared header missing")
    require(page.locator(".footer").count() >= 1, "Footer missing")
    require(page.locator('.site-call-link').count() == 0,
            "One-tap phone control must not appear in the site header")
    require(page.locator('.footer-directions-link[href="contacts.html"]').count() == 1,
            "Footer office address lacks direct Contacts route")
    require(page.locator('.footer-logos a[href="company.html"]').count() == 1,
            "MDIS footer logo must link to local company page")
    dev = page.locator('.site-dev-progress[href="migration-progress.html"]')
    require(dev.count() == 1, "Preview-only DEV progress button missing")
    require(dev.is_visible(), "DEV progress button must be visible in shared header")
    require(page.locator('.site-dev-mobile-link[href="migration-progress.html"]').count() == 1,
            "DEV progress route missing from mobile menu")
    if width > 1080:
        require(page.locator('.site-nav > a[href="contacts.html"]').count() == 1,
                "Contacts must be a visible top-level desktop menu link")
        require(page.locator('.site-nav > a[href="contacts.html"]').is_visible(),
                "Desktop Contacts link is hidden")
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
            if label == "Компания":
                require(group.locator('a[href="contacts.html"]').count() == 1,
                        "Company desktop dropdown has no Contacts link")
            box = group.locator(".site-menu-panel").bounding_box()
            if box:
                require(box["x"] >= -3 and box["x"] + box["width"] <= width + 3,
                        f"{label} panel outside viewport: {box}")
            group.locator("summary").click()
    else:
        mobile = page.locator(".site-mobile-menu")
        mobile.locator(":scope > summary").click()
        require(mobile.get_attribute("open") is not None, "Mobile menu did not open")
        require(mobile.locator('nav.site-mobile-popover > a[href="contacts.html"]').count() == 1,
                "Mobile Contacts direct link missing")
        require(mobile.locator('nav.site-mobile-popover > a[href="contacts.html"]').is_visible(),
                "Mobile Contacts direct link is hidden")
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
            if label == "Компания":
                require(group.locator('a[href="contacts.html"]').count() == 1,
                        "Company mobile dropdown has no Contacts link")
            group.locator("summary").click()
    if filename == "pultex.html":
        require(page.locator('a[href^="https://pultex.pro/wp-content/uploads/"]').count() == 4,
                "PultEx must link four specific manufacturer documents")
        require(page.locator('[role="row"]').count() >= 8,
                "PultEx comparison rows need accessible semantics")
    if filename == "phantom-cross.html":
        require(page.locator('a[href="phantom-monitoring.html"]').filter(
            has_text="Возможности модуля мониторинга").count() == 1,
                "Cross monitoring link must describe the technical page, not a news item")
        for href in ["phantom-asr.html", "support-phantom-cross.html"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"Cross related page missing: {href}")
    if filename == "phantom-monitoring.html":
        require(page.locator("#snmp").count() == 1,
                "Monitoring SNMP architecture anchor missing")
        require(page.locator('a[href="support-phantom-cross.html"]').count() >= 1,
                "Monitoring has no local documentation link")
    if filename == "phantom-asr.html":
        require(page.locator("ol.process > li.process-node").count() == 5,
                "ASR process must preserve five ordered technical steps")
    if filename == "selective-recording.html":
        for href in ["phantom-active.html", "ip-telephony.html",
                     "telephone-recording.html"]:
            require(page.locator(f'a[href="{href}"]').count() >= 1,
                    f"Selective recording missing local route: {href}")
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
        require(page.locator('img.micro-product-image[src="assets/products/phantom-micro-cutout-20261117.svg"]').count() == 1,
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
            src = f"assets/schemes/{img}"
            if img == "protocols-sip-h323.webp":
                src += "?v=20261116-lan123"
            require(page.locator(f'img[src="{src}"]').count() == 1,
                    f"Connection scheme image missing: {img}")
            require(page.locator(f'a.scheme-fullsize[href="{src}"]').count() == 1,
                    f"Full-size connection scheme URL is stale: {img}")
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
    if filename == "contacts.html":
        require(page.locator('.site-nav > a[href="contacts.html"][aria-current="page"]').count() == 1,
                "Contacts current-page navigation state is missing")
        require(page.locator('.hero-phone a[href="tel:+74957833379"]').count() == 0,
                "Contact hero phone should be displayed as text, not trigger a call")
        require(page.locator('.hero-phone').count() == 1 and
                "+7 (495) 783-33-79" in page.locator('.hero-phone').inner_text(),
                "Plain telephone number missing from contact hero")
        require(page.locator('.hero-actions a[href="mailto:support@mdis.ru"]').count() == 1,
                "Support email CTA missing from contact hero")
        require(page.locator('.hero-actions a[href="mailto:sales@mdis.ru"]').count() == 1,
                "Sales email CTA missing from contact hero")
        require(page.locator('main a[href="mailto:sales@mdis.ru"]').count() == 3,
                "Contacts page must expose sales email in cards and common consultation")
        require(page.locator('main a[href="mailto:support@mdis.ru"]').count() == 2,
                "Contacts page lacks technical support email")
        require(page.locator('.contact-card').count() == 2,
                "Two contact departments must be present")
        require(page.locator('.contact-card a[href="requisites.html"]').count() == 1,
                "Sales requisites link missing")
        require(page.locator('.contact-card a[href="support.html"]').count() == 1,
                "Support documentation link missing")
        require(page.locator('.cross-links').count() == 0,
                "Extra links should not appear under extension numbers")
        require(page.locator('main address').count() == 1, "Office address not semantic")
        require("123022" in page.locator('main address').inner_text(),
                "Contact address must use verified index 123022")
        require(page.locator('a[href="https://yandex.com/maps/org/mdis/1055025379/"]').count() == 1,
                "Verified Yandex route link is missing")
        iframe = page.locator('#office-map iframe')
        require(iframe.count() == 1, "Office map iframe must be present on page load")
        require(iframe.get_attribute('src').startswith(
                "https://www.openstreetmap.org/export/embed.html"),
                "Office map source missing on page load")
        require(iframe.get_attribute('loading') == 'eager',
                "Office map should load immediately without user action")
        require(page.locator('#show-office-map').count() == 0,
                "Office map must not require a click to appear")
        require(page.locator('.dept-list > li').count() == 3,
                "Development, production and quality direct extensions missing")
        require("783-33-79" in page.locator('#departments .section-lead').inner_text(),
                "Departments lack main telephone number")
        if width > 600:
            boxes = [page.locator('.contact-card').nth(i).bounding_box() for i in range(2)]
            require(boxes[0] is not None and boxes[1] is not None,
                    "Contact card bounding boxes unavailable")
            require(abs(boxes[0]['height'] - boxes[1]['height']) <= 2,
                    f"Unequal department cards: {boxes}")
        nav = page.locator('nav.solutions-switcher[aria-label="Переход между разделами компании"]')
        require(nav.count() == 1, "Contacts company navigation tape missing")
        require(nav.locator('.solutions-switcher-neighbor--previous[href="requisites.html"]').count() == 1,
                "Contacts previous navigation must lead to requisites")
        require(nav.locator('.solutions-switcher-neighbor--next[href="partners.html"]').count() == 1,
                "Contacts next navigation must lead to partners")
        page.evaluate("window.scrollTo({top: document.body.scrollHeight * 0.65, behavior: 'instant'})")
        page.wait_for_timeout(100)
        metrics = nav.evaluate("""el => ({
            position: getComputedStyle(el).position,
            top: el.getBoundingClientRect().top,
            expected: parseFloat(getComputedStyle(document.documentElement)
                .getPropertyValue('--site-header-height')) || 64,
            headerBottom: document.querySelector('.site-header').getBoundingClientRect().bottom
        })""")
        require(metrics['position'] == 'sticky',
                f"Company navigation tape is not sticky: {metrics}")
        require(abs(metrics['top'] - metrics['headerBottom']) <= 3,
                f"Company navigation tape does not stick below menu: {metrics}")
        page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
        page.wait_for_timeout(100)
        mobile_menu = page.locator(".site-mobile-menu")
        if mobile_menu.get_attribute("open") is not None:
            mobile_menu.locator(":scope > summary").click()
        page.screenshot(path=str(SHOTS / f"contacts-final-{width}-{page.locator('html').get_attribute('data-theme')}.png"),
                        full_page=True, timeout=15000)
        if width == 375 and page.locator('html').get_attribute('data-theme') == 'light':
            page.locator('nav.solutions-switcher .solutions-switcher-control').last.click()
            page.wait_for_url("**/partners.html", timeout=15000)
            page.go_back(wait_until="domcontentloaded", timeout=15000)
            require(page.url.endswith("/contacts.html"),
                    "Contacts next company arrow did not return correctly")
    if filename == "requisites.html":
        downloads = [
            ("assets/requisites/mdis-ooo-mdis.pdf", "Реквизиты_ООО_МДИС.pdf",
             "04372497b5ba585312f6c5fbd8433dad80c2e5494131d92cdc09c16e09d0e7c0"),
            ("assets/requisites/mdis-information-systems.pdf",
             "Реквизиты_ООО_МД_Информационные_Системы.pdf",
             "23d3a51ea49eb88e823d171a4d6ba9eecc1a11441b7c9a0e90a998fac3addd62"),
        ]
        require(page.locator('.doc-card a.open-link[href$=".pdf"]').count() == 2,
                "Expected exactly two PDF requisites downloads")
        require(page.locator('main a[href$=".jpg"], main a[href$=".jpeg"]').count() == 0,
                "JPG requisites downloads must not be shown")
        for href, name, checksum in downloads:
            link = page.locator(f'.doc-card a.open-link[href="{href}"][download="{name}"]')
            require(link.count() == 1, f"Local requisites PDF download missing: {href}")
            if width == 375:
                with page.expect_download(timeout=15000) as download_event:
                    link.click()
                saved = download_event.value
                require(saved.suggested_filename == name,
                        f"Unexpected PDF filename: {saved.suggested_filename}")
                actual = hashlib.sha256(Path(saved.path()).read_bytes()).hexdigest()
                require(actual == checksum, f"Requisites PDF checksum mismatch: {href}")
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


def inspect_mobile_footer_logos(page, width: int):
    """Check visible logo artwork, not only its untransformed anchor layout."""
    if width != 375:
        return
    boxes = page.evaluate("""() => {
        const anchors = [...document.querySelectorAll(
            '#site-footer .footer-logo-band .footer-logos > a'
        )];
        return anchors.map(a => {
            const img = [...a.querySelectorAll('img')].find(i => {
                const r = i.getBoundingClientRect();
                return getComputedStyle(i).display !== 'none' && r.width > 0;
            });
            if (!img) return null;
            const r = img.getBoundingClientRect();
            return {left: r.left, right: r.right, top: r.top, bottom: r.bottom};
        });
    }""")
    require(len(boxes) == 4 and all(box is not None for box in boxes),
            "Four responsive brand logos should remain visible")
    for i, rect in enumerate(boxes):
        require(rect["left"] >= -1 and rect["right"] <= width + 1,
                f"Mobile footer logo {i+1} clips outside viewport: {rect}")
        if i:
            require(rect["left"] >= boxes[i-1]["right"] - 1,
                    f"Mobile footer logos {i} and {i+1} overlap")


def main():
    require(len(PAGES) == len(set(PAGES)),
            "Duplicate HTML pages in browser QA matrix")
    check_local_links()
    verify_original_assets()
    verify_legacy_archives()
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
                                if filename != "migration-progress.html":
                                    inspect_mobile_footer_logos(page, width)
                                inspect_active_underline_hover(page, filename, width)
                                if filename == "solutions.html":
                                    hub_nav = page.locator('nav.solutions-switcher[aria-label="Переход между решениями"]')
                                    require(hub_nav.count() == 1,
                                            "Solutions hub must have one navigation strip immediately after hero")
                                    require(hub_nav.locator('a.solutions-switcher-label[href="solutions.html"]').count() == 1,
                                            "Solutions hub navigation center must link to solutions.html")
                                    require(hub_nav.locator('a.solutions-switcher-neighbor--previous[href="aviation-transport.html"]').count() == 1,
                                            "Solutions hub previous neighbour must be Aviation and Transport")
                                    require(hub_nav.locator('a.solutions-switcher-neighbor--next[href="atom-energy.html"]').count() == 1,
                                            "Solutions hub next neighbour must be Atomic Energy")
                                    require(hub_nav.evaluate("(el) => el.previousElementSibling?.matches('section.hero')"),
                                            "Solutions hub navigation must follow the first-screen hero")
                                    hero_bg = page.locator('main > .hero').evaluate(
                                        "(el) => getComputedStyle(el).backgroundImage")
                                    require("solutions-hero-waves-20261117-v3.webp" in hero_bg,
                                            f"Solutions background overridden by shared CSS: {hero_bg}")
                                    image_ok = page.evaluate("""async () => {
                                        const bg = getComputedStyle(document.querySelector('main > .hero')).backgroundImage;
                                        const url = bg.match(/url\\(["']?([^"')]+)["']?\\)/)?.[1];
                                        if (!url) return false;
                                        const img = new Image();
                                        img.src = url;
                                        try { await img.decode(); return img.naturalWidth >= 1200; }
                                        catch { return false; }
                                    }""")
                                    require(image_ok, "Solutions hero background asset is missing or cannot be decoded")
                                if filename == "services.html":
                                    hero_bg = page.locator('main > .hero').evaluate(
                                        "(el) => getComputedStyle(el).backgroundImage")
                                    require("solutions-hero-waves-20261117-v3.webp" in hero_bg,
                                            f"Services background must match Solutions: {hero_bg}")
                                    require(page.locator('#decision h2').inner_text() == "От задачи – к решению",
                                            "Services slogan unexpectedly changed")
                                    cards = page.locator('#prepare .prepare-list > li')
                                    require(cards.count() == 7, "Services preparation list must contain seven items")
                                    layout = page.locator('#prepare .prepare-list').evaluate("""(el) =>
                                        [...el.children].map((node) => {
                                            const box = node.getBoundingClientRect();
                                            return {x: box.x, y: box.y, width: box.width};
                                        })""")
                                    near = lambda a, b: abs(a - b) < 3
                                    if width > 560:
                                        require(all(near(layout[i]["y"], layout[0]["y"]) for i in (1, 2))
                                                and near(layout[3]["y"], layout[4]["y"])
                                                and near(layout[5]["y"], layout[6]["y"])
                                                and layout[0]["y"] < layout[3]["y"] < layout[5]["y"],
                                                f"Preparation grid must have 3 + 2 + 2 cards: {layout}")
                                        require(all(near(layout[i]["width"], layout[0]["width"]) for i in (1, 2)),
                                                f"Top row must have three equally short cards: {layout}")
                                        require(layout[4]["width"] > layout[3]["width"]
                                                and layout[5]["width"] > layout[6]["width"]
                                                and not near(layout[3]["width"], layout[0]["width"]),
                                                f"Preparation row joints must be staggered: {layout}")
                                    else:
                                        require(all(near(layout[i]["width"], layout[0]["width"]) for i in range(1, 7))
                                                and all(layout[i]["y"] < layout[i+1]["y"] for i in range(6)),
                                                f"Mobile preparation cards must form one column: {layout}")
                                    require(page.locator('#prepare .section-note').count() == 0,
                                            "Redundant preparation note unexpectedly returned")
                                if filename in ("news.html", "contacts.html"):
                                    expected_asset = ("news-hero-original-20261117.webp"
                                                      if filename == "news.html"
                                                      else "contacts-hero-original-20261117.webp")
                                    hero_bg = page.locator("main > .hero").evaluate(
                                        "(el) => getComputedStyle(el).backgroundImage")
                                    require(expected_asset in hero_bg,
                                            f"{filename}: original background overridden by shared CSS: {hero_bg}")
                                    image_ok = page.evaluate("""async (fileName) => {
                                        const picture = new Image();
                                        picture.src = "assets/backgrounds/" + fileName;
                                        try {
                                            await picture.decode();
                                            return picture.naturalWidth >= 1600 && picture.naturalHeight >= 880;
                                        } catch { return false; }
                                    }""", expected_asset)
                                    require(image_ok,
                                            f"{filename}: original WebP background not loaded or damaged")
                                if filename == "phantom-home.html":
                                    require(page.locator('.contact-area #contact-form').count() == 1,
                                            "Homepage must retain its original engineer consultation form")
                                elif filename != "migration-progress.html":
                                    require(page.locator('main > section.site-consultation').count() == 1,
                                            "Every public-facing page must end with one shared engineer consultation section")
                                    require(page.locator('main > section.site-consultation').is_visible(),
                                            "Shared engineer consultation is hidden")
                                    require(page.locator('#site-consultation-form').count() == 1,
                                            "Shared engineer consultation form is missing")
                                if filename == "phantom-home.html":
                                    switcher = page.locator("a.solutions-switcher-label")
                                    require(switcher.count() == 1, "Solutions hub link is missing or duplicated")
                                    require(switcher.get_attribute("href") == "solutions.html",
                                            "All solutions link must open the local industry hub")
                                    require(page.locator("#industries").count() == 1,
                                            "Homepage industries section must remain available")
                                if filename == "support-stantsiya-zapisi.html":
                                    require(page.locator('main a[href="faq.html"]').count() >= 1,
                                            "Station support FAQ link is missing")
                                    require(page.locator('main a[href$=".pdf"]').count() == 2,
                                            "Station support must expose two local PDF originals")
                                if filename == "privacy-policy.html":
                                    require(page.locator("article.policy-content section.policy-section").count() == 8,
                                            "Privacy policy must retain eight legal sections")
                                    require(page.locator("article.policy-content p.clause").count() == 22,
                                            "Privacy policy must retain 22 legal clauses")
                                    require(page.locator('article.policy-content a[href="cookie-policy.html"]').count() >= 2,
                                            "Privacy policy must link locally to cookie policy")
                                if filename == "cookie-policy.html":
                                    require(page.locator("main section.legal-section").count() == 8,
                                            "Cookie policy must retain eight legal sections")
                                    require(page.locator('main nav.legal-index a[href^="#policy-section-"]').count() == 8,
                                            "Cookie policy contents links must cover all eight sections")
                                    require(page.locator('main a[href="privacy-policy.html"]').count() >= 1,
                                            "Cookie policy must link locally to privacy policy")
                                if filename == "migration-progress.html":
                                    rows = page.locator("tr.page-row")
                                    require(rows.count() == 56, "Migration registry must list exactly 56 actual site pages")
                                    page_numbers = page.locator("tr.page-row .page-number").all_text_contents()
                                    require(page_numbers == [f"{i:02d}" for i in range(1, 57)],
                                            "Registry page numbers must run consecutively from 01 to 56")
                                    require(page.locator(".group-index").count() == 0,
                                            "Section headings should not display ordinal numbers")
                                    require(page.locator(".group-row th[colspan='7']").count() == 7,
                                            "Seven actual site categories must span seven table columns")
                                    require(page.locator('tbody[data-section="Архивные HTML-дубли"]').count() == 0,
                                            "Historical duplicate category must be completely absent")
                                    require(page.locator('[data-legacy]').count() == 0,
                                            "Historical duplicate attributes must not appear in the progress table")
                                    filter_counts = page.locator('.filter-count').all_text_contents()
                                    require(filter_counts == ["56", "5", "3", "48"],
                                            "Filters must count only the 56 relevant pages")
                                    metric_values = page.locator(".metrics .metric").all_text_contents()
                                    require(len(metric_values) == 4
                                            and "56" in metric_values[0] and "Страниц сайта" in metric_values[0]
                                            and "5" in metric_values[1] and "Готовы" in metric_values[1]
                                            and "3" in metric_values[2] and "В работе" in metric_values[2]
                                            and "51" in metric_values[3] and "Не готовы" in metric_values[3],
                                            "Migration dashboard must show all four current summary metrics")
                                    require(page.locator(".metric--not-ready").get_attribute("title") == "3 страницы в работе и 48 без статуса готовности",
                                            "Not-ready total must explain that it includes active pages")
                                    ready_metric_color = page.locator(".metric--ready strong").evaluate("(el) => getComputedStyle(el).color")
                                    ready_check_color = page.locator(".check.ready").first.evaluate("(el) => getComputedStyle(el).color")
                                    require(ready_metric_color == ready_check_color,
                                            "Ready counter must match the green completion checkmarks")
                                    work_metric_color = page.locator(".metric--in-work strong").evaluate("(el) => getComputedStyle(el).color")
                                    work_label_color = page.locator(".work-status").first.evaluate("(el) => getComputedStyle(el).color")
                                    require(work_metric_color == work_label_color,
                                            "In-progress counter must match the yellow work status")
                                    neutral_metric_color = page.locator(".metrics .metric").first.locator("strong").evaluate("(el) => getComputedStyle(el).color")
                                    not_ready_metric_color = page.locator(".metric--not-ready strong").evaluate("(el) => getComputedStyle(el).color")
                                    require(neutral_metric_color == not_ready_metric_color,
                                            "Totals must remain visually neutral")
                                    require(page.locator("footer.footer").count() == 0,
                                            "Progress registry must not render the site footer")
                                    require(page.locator(".site-consultation").count() == 0,
                                            "Progress registry must not display an engineer consultation form")
                                    require(page.locator('script[src*="site-consultation.js"]').count() == 0,
                                            "Progress registry must not load consultation injection")
                                    require(page.locator("header.site-header").count() == 1,
                                            "Progress registry must preserve the shared site header")
                                    header_titles = page.locator(".registry thead th").all_text_contents()
                                    require(header_titles == ["№", "Страница", "Старый сайт", "Новый сайт", "Код", "Перенесена", "Статус"],
                                            "Migration comparison table must have seven clear column names")
                                    ready_rows = page.locator('tr.page-row[data-ready="true"]')
                                    require(ready_rows.count() == 5,
                                            "Only five agreed pages must be ready")
                                    ready_files = ready_rows.locator(".page-file").all_text_contents()
                                    require(set(ready_files) == {"phantom-home.html", "solutions.html", "services.html", "contacts.html", "electroenergetika.html"},
                                            "Ready flags must match homepage, Solutions, Services, Contacts and Electricity")
                                    require(ready_rows.locator(".check.ready").count() == 5,
                                            "Each ready page must have a visible checkmark")
                                    require(ready_rows.locator(".ready-status").count() == 5,
                                            "Each finished page needs a textual ready status")
                                    require(all(text.strip() == "✓Готово" for text in ready_rows.locator(".ready-status").all_text_contents()),
                                            "Ready statuses must display a green check followed by the word Готово")
                                    require(page.locator(".registry thead th.status-heading").inner_text() == "Статус",
                                            "The most important status column must be visibly highlighted")
                                    status_header_style = page.locator(".registry thead th.status-heading").evaluate(
                                        "(el) => ({background: getComputedStyle(el).backgroundColor, weight: parseFloat(getComputedStyle(el).fontWeight), shadow: getComputedStyle(el).boxShadow})")
                                    standard_header_style = page.locator(".registry thead th").first.evaluate(
                                        "(el) => ({background: getComputedStyle(el).backgroundColor, weight: parseFloat(getComputedStyle(el).fontWeight)})")
                                    require(status_header_style["background"] == standard_header_style["background"]
                                            and status_header_style["weight"] > standard_header_style["weight"]
                                            and status_header_style["shadow"] != "none",
                                            "Status heading must be prominent but share the table header background")
                                    status_cell = ready_rows.first.locator('td[data-label="Статус"]')
                                    status_cell_background = status_cell.evaluate("(el) => getComputedStyle(el).backgroundColor")
                                    ordinary_cell_background = ready_rows.first.locator('td[data-label="Код"]').evaluate("(el) => getComputedStyle(el).backgroundColor")
                                    require(status_cell_background == ordinary_cell_background,
                                            "Status cells must share row backgrounds so the column is not visually detached")
                                    ready_pill_background = ready_rows.first.locator(".ready-status").evaluate("(el) => getComputedStyle(el).backgroundColor")
                                    work_pill_background = page.locator(".work-status").first.evaluate("(el) => getComputedStyle(el).backgroundColor")
                                    require(ready_pill_background != status_cell_background
                                            and work_pill_background != status_cell_background
                                            and ready_pill_background != work_pill_background,
                                            "Ready and in-progress labels must be distinct compact status pills")
                                    if width > 900:
                                        status_separator = float(status_cell.evaluate("(el) => getComputedStyle(el).borderLeftWidth").replace("px", ""))
                                        status_right_separator = float(status_cell.evaluate("(el) => getComputedStyle(el).borderRightWidth").replace("px", ""))
                                        header_left = float(page.locator(".registry thead th.status-heading").evaluate("(el) => getComputedStyle(el).borderLeftWidth").replace("px", ""))
                                        header_right = float(page.locator(".registry thead th.status-heading").evaluate("(el) => getComputedStyle(el).borderRightWidth").replace("px", ""))
                                        ordinary_separator = float(ready_rows.first.locator('td[data-label="Код"]').evaluate("(el) => getComputedStyle(el).borderLeftWidth").replace("px", ""))
                                        title_separator = float(ready_rows.first.locator('th[scope="row"]').evaluate("(el) => getComputedStyle(el).borderLeftWidth").replace("px", ""))
                                        require(ordinary_separator == 1 and title_separator == 1
                                                and status_separator == 3 and status_right_separator == 3
                                                and header_left == 3 and header_right == 3,
                                                "Columns need thin 1px separators and 3px borders on both sides of Status")
                                    else:
                                        require(status_cell.evaluate("(el) => getComputedStyle(el).borderLeftWidth") in ("0px", "0"),
                                                "Mobile cards must not have a separating vertical border")

                                    require(page.locator('a.link.old.row-action').count() == 56,
                                            "All 56 site pages must have an old-site action")
                                    require(page.locator('a.link.stage.row-action').count() == 56,
                                            "Every canonical row must have a new-site action")
                                    require(page.locator('a.link.github.row-action').count() == 56,
                                            "All 56 site pages must have a code action")
                                    require(page.locator('a.link.old').first.inner_text().startswith("Открыть"),
                                            "Old-site links must use an action label")
                                    require(page.locator('a.link.stage').first.inner_text().startswith("Открыть"),
                                            "New-site links must use an action label")
                                    require(page.locator('a.link.github').first.inner_text().startswith("Посмотреть"),
                                            "Code links must use an action label")
                                    require("старую версию" in page.locator('a.link.old').first.get_attribute("aria-label"),
                                            "Old-site action must explain its destination accessibly")
                                    require("новую версию" in page.locator('a.link.stage').first.get_attribute("aria-label"),
                                            "New-site action must explain its destination accessibly")
                                    require(page.locator('a.link.stage[href^="https://relay.mixerland.ru:8443/mdis-preview/"]').count() == 56,
                                            "All 56 canonical rows must keep their AEZA URLs")
                                    require(page.get_by_role("heading", name="Как сравнить страницы").count() == 1,
                                            "Registry must explain how to compare the pages")
                                    require(page.locator(".guide-steps li").count() == 3,
                                            "Comparison guide must have three clear steps")
                                    require(page.locator('a.hero-jump[href="#registry"]').count() == 1,
                                            "Hero must provide a direct link to the table")
                                    ready_color = ready_rows.locator(".check.ready").first.evaluate("(el) => getComputedStyle(el).color")
                                    transferred_color = page.locator(".check:not(.ready)").first.evaluate("(el) => getComputedStyle(el).color")
                                    require(ready_color == transferred_color,
                                            "Ready checks must use the same green color as transferred checks")
                                    if width <= 900:
                                        mobile_display = rows.first.evaluate("(el) => getComputedStyle(el).display")
                                        require(mobile_display == "grid",
                                                "Registry rows must become readable cards on small screens")
                                        require(page.locator('.registry').evaluate("(el) => el.getBoundingClientRect().width") <= width,
                                                "Mobile registry must fit inside the viewport")
                                    page.locator("#page-search").fill("контакты")
                                    require(page.locator("tr.page-row:visible").count() == 1,
                                            "Registry text search does not isolate Contacts")
                                    page.locator("#page-search").fill("02")
                                    require(page.locator('tr.page-row').filter(has=page.locator('.page-number', has_text="02")).first.is_visible(),
                                            "Registry text search must support row numbers")
                                    page.locator("#page-search").fill("")
                                    page.locator('button[data-filter="ready"]').click()
                                    require(page.locator("tr.page-row:visible").count() == 5,
                                            "Ready filter must show five pages")
                                    page.locator('button[data-filter="pending"]').click()
                                    require(page.locator("tr.page-row:visible").count() == 3,
                                            "In-progress filter must include only pages 04, 05 and 06")
                                    work_rows = page.locator('tr.page-row[data-progress="true"]')
                                    require(work_rows.count() == 3,
                                            "Exactly three explicitly active pages expected")
                                    work_files = work_rows.locator('.page-file').all_text_contents()
                                    require(set(work_files) == {"news.html", "support.html", "company.html"},
                                            "Work markers must be on pages 04, 05, and 06")
                                    require(work_rows.locator('.work-status .work-dot').count() == 3,
                                            "All in-progress pages need a yellow dot")
                                    require(work_rows.locator('.work-status').first.inner_text().strip() == "В работе",
                                            "In-progress badge must be self-explanatory")
                                    require(page.locator(".legend-work").count() == 1,
                                            "Yellow status must be explained in the legend")
                                    page.locator('button[data-filter="queued"]').click()
                                    require(page.locator("tr.page-row:visible").count() == 48,
                                            "Unassigned filter should show remaining 48 pages")
                                    require(page.locator('button[data-filter="archive"]').count() == 0,
                                            "Archive filter must not be present")
                                    page.locator('button[data-filter="all"]').click()
                                    require(page.locator("tr.page-row:visible").count() == 56,
                                            "All filter must show only the 56 relevant pages")
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
