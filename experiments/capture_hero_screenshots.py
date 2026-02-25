#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright


COOKIE_ACTION_SELECTORS = [
    "#BorlabsCookieBox #CookieBoxSaveButton",
    "#BorlabsCookieBox ._brlbs-btn-accept-all",
    "#BorlabsCookieBox #CookiePrefSave",
    "#BorlabsCookieBox a:has-text('Speichern')",
    "#BorlabsCookieBox a:has-text('Alle akzeptieren')",
    "#BorlabsCookieBox a:has-text('Nur essenzielle Cookies akzeptieren')",
]

COOKIE_OVERLAY_SELECTORS = [
    "#BorlabsCookieBox ._brlbs-box-wrap",
    "#BorlabsCookieBox .cookie-box",
    "#BorlabsCookieBox .middle-center.show-cookie-box",
]


def parse_viewport(value: str) -> Tuple[int, int]:
    width, height = value.lower().split("x", 1)
    return int(width), int(height)


def dismiss_cookie_banner(page) -> str:
    def overlay_visible() -> bool:
        return bool(
            page.evaluate(
                """(selectors) => selectors.some((selector) =>
                    Array.from(document.querySelectorAll(selector)).some((el) => {
                        const style = window.getComputedStyle(el);
                        const rect = el.getBoundingClientRect();
                        return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0' && rect.width > 0 && rect.height > 0;
                    })
                )""",
                COOKIE_OVERLAY_SELECTORS,
            )
        )

    box = page.locator("#BorlabsCookieBox")
    if box.count() == 0:
        return "not-found"

    for _ in range(10):
        if overlay_visible():
            break
        page.wait_for_timeout(400)
    else:
        return "not-visible"

    for selector in COOKIE_ACTION_SELECTORS:
        candidate = page.locator(selector)
        if candidate.count() == 0:
            continue
        try:
            candidate.first.click(timeout=1800, force=True)
            page.wait_for_timeout(700)
            if not overlay_visible():
                return f"clicked:{selector}"
        except PlaywrightError:
            continue

    page.evaluate(
        """() => {
            for (const selector of [
                '#BorlabsCookieBox',
                '.BorlabsCookie',
                '._brlbs-box-wrap',
                '.middle-center.show-cookie-box'
            ]) {
                for (const el of document.querySelectorAll(selector)) {
                    el.remove();
                }
            }
            document.body.classList.remove('borlabs-position-fix');
        }"""
    )
    page.wait_for_timeout(200)
    if overlay_visible():
        raise RuntimeError("Cookie banner visible, but no dismiss action succeeded")
    return "fallback-removed"


def measure_layout(page) -> Dict[str, object]:
    return page.evaluate(
        """() => {
          const hero = document.querySelector('.flyntComponent[is="flynt-hero-image-header"] .container-background');
          const firstContent = document.querySelector('.flyntComponent.componentSpacing');
          return {
            heroHeight: hero ? Math.round(hero.getBoundingClientRect().height) : null,
            firstContentTop: firstContent ? Math.round(firstContent.getBoundingClientRect().top) : null
          };
        }"""
    )


def capture_variant(page, url: str, output_path: Path) -> Dict[str, object]:
    page.goto(url, wait_until="networkidle", timeout=60000)
    cookie_action = dismiss_cookie_banner(page)
    page.wait_for_timeout(500)
    page.screenshot(path=str(output_path), full_page=False)
    metrics = measure_layout(page)
    metrics["cookie_action"] = cookie_action
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture hero screenshots with cookie banner dismissed"
    )
    parser.add_argument("--url", required=True, help="Page URL to capture")
    parser.add_argument("--output-prefix", required=True, help="Output filename prefix")
    parser.add_argument(
        "--output-dir", default="experiments/screenshots", help="Screenshot directory"
    )
    parser.add_argument("--desktop", default="1280x800", help="Desktop viewport WxH")
    parser.add_argument("--mobile", default="390x844", help="Mobile viewport WxH")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    desktop_w, desktop_h = parse_viewport(args.desktop)
    mobile_w, mobile_h = parse_viewport(args.mobile)

    result: Dict[str, Dict[str, object]] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        desktop_page = browser.new_page(
            viewport={"width": desktop_w, "height": desktop_h}
        )
        desktop_path = out_dir / f"{args.output_prefix}-desktop.png"
        result["desktop"] = capture_variant(desktop_page, args.url, desktop_path)
        desktop_page.close()

        mobile_page = browser.new_page(viewport={"width": mobile_w, "height": mobile_h})
        mobile_path = out_dir / f"{args.output_prefix}-mobile.png"
        result["mobile"] = capture_variant(mobile_page, args.url, mobile_path)
        mobile_page.close()

        browser.close()

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
