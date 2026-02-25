#!/usr/bin/env python3
"""
Partieller Website-Klon für studiumplus.de

Playwright-basiertes Skript zum Klonen ausgewählter Bereiche von studiumplus.de.
Speichert gerenderte HTML-Seiten, Bilder, CSS/JS lokal und aktualisiert die registry.json.

Aufruf:
    python scripts/clone.py <URL> [<URL> ...] [--max-depth N] [--delay S] [--output-dir DIR]
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_FILE = SCRIPT_DIR / "clone.log"

logger = logging.getLogger("clone")
logger.setLevel(logging.DEBUG)

_fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s")

_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(_fmt)
logger.addHandler(_fh)

_sh = logging.StreamHandler()
_sh.setLevel(logging.INFO)
_sh.setFormatter(_fmt)
logger.addHandler(_sh)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SITE_ORIGIN = "https://studiumplus.de"
SHARED_ASSETS_DIR = "_shared_assets"
PAGE_ASSETS_DIR = "_assets"
THUMBNAIL_DIR = "thumbnails"
REGISTRY_FILE = "registry.json"

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".svg", ".webp", ".gif"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalise_url(url: str) -> str:
    """Return a canonical URL without fragment, with trailing slash for paths."""
    parsed = urlparse(url)
    path = parsed.path
    # Ensure trailing slash for directory-like paths (no file extension)
    if not path.endswith("/") and "." not in path.split("/")[-1]:
        path += "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _url_to_local_path(url: str, output_dir: Path) -> Path:
    """Map a URL path to a local filesystem path."""
    parsed = urlparse(url)
    rel = parsed.path.lstrip("/")
    if rel.endswith("/"):
        rel = rel + "index.html"
    elif "." not in rel.split("/")[-1]:
        rel = rel + "/index.html"
    return output_dir / rel


def _relative_path(from_file: Path, to_file: Path) -> str:
    """Compute the relative path from *from_file* to *to_file*."""
    return os.path.relpath(to_file, from_file.parent)


def _slug_from_url(url: str) -> str:
    """Derive a short slug from a URL path for use as an area id."""
    path = urlparse(url).path.strip("/")
    return path.split("/")[-1] if path else "root"


def _is_same_origin(url: str) -> bool:
    """Check whether *url* belongs to studiumplus.de."""
    parsed = urlparse(url)
    return parsed.netloc in ("studiumplus.de", "www.studiumplus.de", "")


def _is_external_resource(url: str) -> bool:
    """Return True for resources hosted on external CDNs / domains."""
    if not url or url.startswith("data:"):
        return True
    parsed = urlparse(url)
    if not parsed.netloc:
        return False  # relative URL → same origin
    return parsed.netloc not in ("studiumplus.de", "www.studiumplus.de")


def _asset_filename(url: str, existing: set) -> str:
    """Generate a unique local filename for an asset URL."""
    parsed = urlparse(url)
    base = Path(parsed.path).name or "asset"
    if base in existing:
        name, ext = os.path.splitext(base)
        i = 1
        while f"{name}_{i}{ext}" in existing:
            i += 1
        base = f"{name}_{i}{ext}"
    existing.add(base)
    return base


# ---------------------------------------------------------------------------
# Cookie-banner handling
# ---------------------------------------------------------------------------


def _dismiss_cookie_banner(page) -> None:
    """Try to close a cookie/consent banner if visible."""
    selectors = [
        "button:has-text('Alle akzeptieren')",
        "button:has-text('Akzeptieren')",
        "button:has-text('Accept')",
        "button:has-text('Accept all')",
        "button:has-text('Alle Cookies akzeptieren')",
        "button:has-text('Zustimmen')",
        "[id*='cookie'] button",
        "[class*='cookie'] button",
        "[id*='consent'] button",
        "[class*='consent'] button",
        ".cc-dismiss",
        ".cc-allow",
    ]
    for sel in selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_visible():
                btn.click()
                logger.info("Cookie-Banner geschlossen via Selector: %s", sel)
                page.wait_for_timeout(500)
                return
        except Exception:
            continue


# ---------------------------------------------------------------------------
# Asset downloading helpers
# ---------------------------------------------------------------------------


def _download_image(page, url: str, dest: Path) -> bool:
    """Download an image via Playwright's request context and save to *dest*."""
    try:
        resp = page.request.get(url)
        if resp.ok:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.body())
            logger.debug("Bild gespeichert: %s → %s", url, dest)
            return True
        else:
            logger.warning("Bild-Download fehlgeschlagen (%s): %s", resp.status, url)
    except Exception as exc:
        logger.warning("Bild-Download Fehler für %s: %s", url, exc)
    return False


def _download_text_asset(page, url: str, dest: Path) -> bool:
    """Download a CSS/JS text asset."""
    try:
        resp = page.request.get(url)
        if resp.ok:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.body())
            logger.debug("Asset gespeichert: %s → %s", url, dest)
            return True
        else:
            logger.warning("Asset-Download fehlgeschlagen (%s): %s", resp.status, url)
    except Exception as exc:
        logger.warning("Asset-Download Fehler für %s: %s", url, exc)
    return False


# ---------------------------------------------------------------------------
# HTML rewriting
# ---------------------------------------------------------------------------


def _rewrite_html(
    html: str,
    page_url: str,
    page_file: Path,
    output_dir: Path,
    prefix: str,
    downloaded_images: dict,
    downloaded_assets: dict,
) -> str:
    """Rewrite image srcs, CSS/JS hrefs, and internal links in *html*."""
    soup = BeautifulSoup(html, "lxml")

    # --- images ---
    for tag in soup.find_all(["img", "source"]):
        for attr in ("src", "data-src", "srcset"):
            val = tag.get(attr)
            if not val:
                continue
            # srcset can contain multiple URLs
            if attr == "srcset":
                parts = []
                for entry in val.split(","):
                    entry = entry.strip()
                    if not entry:
                        continue
                    tokens = entry.split()
                    src = tokens[0]
                    rest = " ".join(tokens[1:])
                    abs_src = urljoin(page_url, src)
                    if abs_src in downloaded_images:
                        local = _relative_path(page_file, downloaded_images[abs_src])
                        parts.append(f"{local} {rest}".strip())
                    else:
                        parts.append(entry)
                tag[attr] = ", ".join(parts)
            else:
                abs_src = urljoin(page_url, val)
                if abs_src in downloaded_images:
                    tag[attr] = _relative_path(page_file, downloaded_images[abs_src])

    # --- CSS links ---
    for tag in soup.find_all("link", rel="stylesheet"):
        href = tag.get("href")
        if not href:
            continue
        abs_href = urljoin(page_url, href)
        if abs_href in downloaded_assets:
            tag["href"] = _relative_path(page_file, downloaded_assets[abs_href])

    # --- JS scripts ---
    for tag in soup.find_all("script", src=True):
        src = tag["src"]
        abs_src = urljoin(page_url, src)
        if abs_src in downloaded_assets:
            tag["src"] = _relative_path(page_file, downloaded_assets[abs_src])

    # --- internal links ---
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        abs_href = urljoin(page_url, href)
        parsed = urlparse(abs_href)
        if not _is_same_origin(abs_href):
            tag["target"] = "_blank"
            tag["rel"] = "noopener"
            continue
        # Check if the link is within the cloned prefix
        norm_path = parsed.path
        if not norm_path.endswith("/") and "." not in norm_path.split("/")[-1]:
            norm_path += "/"
        if norm_path.startswith(prefix):
            # Rewrite to local relative path
            local_target = _url_to_local_path(abs_href, output_dir)
            tag["href"] = _relative_path(page_file, local_target)
        else:
            # Link outside cloned area → keep absolute original URL
            tag["href"] = abs_href
            tag["target"] = "_blank"
            tag["rel"] = "noopener"

    # --- background images in style attributes ---
    for tag in soup.find_all(style=True):
        style = tag["style"]
        urls_in_style = re.findall(r'url\(["\']?(.*?)["\']?\)', style)
        for raw_url in urls_in_style:
            abs_url = urljoin(page_url, raw_url)
            if abs_url in downloaded_images:
                local = _relative_path(page_file, downloaded_images[abs_url])
                style = style.replace(raw_url, local)
        tag["style"] = style

    return str(soup)


# ---------------------------------------------------------------------------
# Core cloning logic
# ---------------------------------------------------------------------------


class SiteCloner:
    """Clones a subtree of studiumplus.de using Playwright."""

    def __init__(self, output_dir: Path, max_depth: int = 5, delay: float = 1.0):
        self.output_dir = output_dir.resolve()
        self.max_depth = max_depth
        self.delay = delay
        self.visited: set[str] = set()
        self.downloaded_images: dict[str, Path] = {}  # abs URL → local Path
        self.downloaded_assets: dict[str, Path] = {}  # abs URL → local Path
        self._image_names: set[str] = set()  # track filenames per page dir
        self._asset_names: set[str] = set()  # track shared asset filenames
        self.pages: list[dict] = []

    # ---- public API ----

    def clone_area(self, start_url: str) -> dict:
        """Clone an entire area starting at *start_url*. Returns area dict for registry."""
        start_url = _normalise_url(start_url)
        prefix = urlparse(start_url).path  # e.g. /duales-studium/.../
        slug = _slug_from_url(start_url)
        local_root = urlparse(start_url).path.strip("/") + "/"

        logger.info("=== Starte Klon-Bereich: %s ===", start_url)

        self.visited.clear()
        self.pages.clear()
        self._image_names.clear()

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = context.new_page()

            # BFS crawl
            queue: list[tuple[str, int]] = [(start_url, 0)]
            thumbnail_path: str | None = None

            while queue:
                url, depth = queue.pop(0)
                url = _normalise_url(url)
                if url in self.visited:
                    continue
                if depth > self.max_depth:
                    continue
                self.visited.add(url)

                logger.info("Lade Seite [Tiefe %d]: %s", depth, url)
                try:
                    resp = page.goto(url, wait_until="networkidle", timeout=30000)
                    if resp is None or resp.status >= 400:
                        status = resp.status if resp else "keine Antwort"
                        logger.warning("HTTP-Fehler (%s): %s – übersprungen", status, url)
                        continue
                except Exception as exc:
                    logger.warning("Fehler beim Laden von %s: %s – übersprungen", url, exc)
                    continue

                # Cookie-Banner schließen (nur beim ersten Aufruf nötig, aber sicherheitshalber immer)
                _dismiss_cookie_banner(page)
                page.wait_for_timeout(500)

                # Screenshot for thumbnail (only for the start URL)
                if url == start_url:
                    thumb_file = self.output_dir / THUMBNAIL_DIR / f"{slug}.png"
                    thumb_file.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(thumb_file), full_page=False)
                    thumbnail_path = f"{THUMBNAIL_DIR}/{slug}.png"
                    logger.info("Thumbnail erstellt: %s", thumb_file)

                # Get rendered HTML
                html = page.content()
                now_str = datetime.now(timezone.utc).isoformat()

                # Determine local file path
                page_file = _url_to_local_path(url, self.output_dir)
                page_file.parent.mkdir(parents=True, exist_ok=True)

                # Extract and download images
                self._download_page_images(page, html, url, page_file)

                # Extract and download CSS/JS from studiumplus.de
                self._download_shared_assets(page, html, url)

                # Rewrite HTML
                rewritten = _rewrite_html(
                    html, url, page_file, self.output_dir,
                    prefix, self.downloaded_images, self.downloaded_assets,
                )
                # Insert clone comment
                comment = f"<!-- Cloned from: {url} at {now_str} -->\n"
                rewritten = comment + rewritten

                page_file.write_text(rewritten, encoding="utf-8")
                logger.info("Seite gespeichert: %s", page_file)

                # Get page title
                title = page.title() or slug

                self.pages.append({
                    "source_url": url,
                    "local_path": str(page_file.relative_to(self.output_dir)),
                    "title": title,
                })

                # Extract links for BFS
                if depth < self.max_depth:
                    links = page.eval_on_selector_all(
                        "a[href]",
                        "els => els.map(e => e.href)",
                    )
                    for link in links:
                        norm = _normalise_url(link)
                        parsed = urlparse(norm)
                        if not _is_same_origin(norm):
                            continue
                        if not parsed.path.startswith(prefix):
                            continue
                        if norm not in self.visited:
                            queue.append((norm, depth + 1))

                # Rate-limiting
                if self.delay > 0:
                    time.sleep(self.delay)

            browser.close()

        area = {
            "id": slug,
            "label": self.pages[0]["title"] if self.pages else slug,
            "source_url": start_url,
            "local_path": local_root,
            "thumbnail": thumbnail_path or "",
            "cloned_at": datetime.now(timezone.utc).isoformat(),
            "pages_count": len(self.pages),
            "pages": list(self.pages),
        }
        logger.info("Bereich abgeschlossen: %s (%d Seiten)", slug, len(self.pages))
        return area

    # ---- private helpers ----

    def _download_page_images(self, page, html: str, page_url: str, page_file: Path):
        """Find and download all images referenced on the page."""
        soup = BeautifulSoup(html, "lxml")
        assets_dir = page_file.parent / PAGE_ASSETS_DIR
        names: set[str] = set()

        image_urls: set[str] = set()

        for tag in soup.find_all(["img", "source"]):
            for attr in ("src", "data-src", "srcset"):
                val = tag.get(attr)
                if not val:
                    continue
                if attr == "srcset":
                    for entry in val.split(","):
                        entry = entry.strip()
                        if entry:
                            image_urls.add(entry.split()[0])
                else:
                    image_urls.add(val)

        # Also capture background-image in inline styles
        for tag in soup.find_all(style=True):
            for raw_url in re.findall(r'url\(["\']?(.*?)["\']?\)', tag["style"]):
                image_urls.add(raw_url)

        for raw in image_urls:
            abs_url = urljoin(page_url, raw)
            if abs_url in self.downloaded_images:
                continue
            if _is_external_resource(abs_url):
                continue
            # Check if it looks like an image
            parsed_path = urlparse(abs_url).path.lower()
            ext = os.path.splitext(parsed_path)[1]
            if ext and ext not in SUPPORTED_IMAGE_EXTENSIONS:
                continue
            # If no extension, still attempt download (could be a dynamic image endpoint)

            fname = _asset_filename(abs_url, names)
            dest = assets_dir / fname
            if _download_image(page, abs_url, dest):
                self.downloaded_images[abs_url] = dest

    def _download_shared_assets(self, page, html: str, page_url: str):
        """Download CSS/JS from studiumplus.de into _shared_assets/."""
        soup = BeautifulSoup(html, "lxml")
        shared_dir = self.output_dir / SHARED_ASSETS_DIR

        # CSS
        for tag in soup.find_all("link", rel="stylesheet"):
            href = tag.get("href")
            if not href:
                continue
            abs_href = urljoin(page_url, href)
            if abs_href in self.downloaded_assets:
                continue
            if _is_external_resource(abs_href):
                continue
            fname = _asset_filename(abs_href, self._asset_names)
            dest = shared_dir / fname
            if _download_text_asset(page, abs_href, dest):
                self.downloaded_assets[abs_href] = dest

        # JS
        for tag in soup.find_all("script", src=True):
            src = tag["src"]
            abs_src = urljoin(page_url, src)
            if abs_src in self.downloaded_assets:
                continue
            if _is_external_resource(abs_src):
                continue
            fname = _asset_filename(abs_src, self._asset_names)
            dest = shared_dir / fname
            if _download_text_asset(page, abs_src, dest):
                self.downloaded_assets[abs_src] = dest


# ---------------------------------------------------------------------------
# Registry management
# ---------------------------------------------------------------------------


def load_registry(output_dir: Path) -> dict:
    """Load or initialise registry.json."""
    registry_path = output_dir / REGISTRY_FILE
    if registry_path.exists():
        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "source": SITE_ORIGIN,
        "last_updated": "",
        "areas": [],
    }


def save_registry(output_dir: Path, registry: dict) -> None:
    """Write registry.json atomically."""
    registry_path = output_dir / REGISTRY_FILE
    registry["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    logger.info("Registry aktualisiert: %s", registry_path)


def upsert_area(registry: dict, area: dict) -> None:
    """Insert or update an area in the registry (idempotent)."""
    for i, existing in enumerate(registry["areas"]):
        if existing["source_url"] == area["source_url"]:
            registry["areas"][i] = area
            logger.info("Bereich aktualisiert in Registry: %s", area["id"])
            return
    registry["areas"].append(area)
    logger.info("Bereich hinzugefügt in Registry: %s", area["id"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Partieller Klon von studiumplus.de-Bereichen",
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="Start-URLs der zu klonenden Bereiche",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximale Crawl-Tiefe (Default: 5)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Verzögerung zwischen Seitenaufrufen in Sekunden (Default: 1.0)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Ausgabeverzeichnis (Default: aktuelles Verzeichnis)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    registry = load_registry(output_dir)

    cloner = SiteCloner(
        output_dir=output_dir,
        max_depth=args.max_depth,
        delay=args.delay,
    )

    for url in args.urls:
        try:
            area = cloner.clone_area(url)
            upsert_area(registry, area)
        except Exception as exc:
            logger.error("Fehler beim Klonen von %s: %s", url, exc, exc_info=True)

    save_registry(output_dir, registry)
    logger.info("=== Klonen abgeschlossen ===")


if __name__ == "__main__":
    main()
