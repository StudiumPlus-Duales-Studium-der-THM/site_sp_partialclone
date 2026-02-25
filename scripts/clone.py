#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import posixpath
import re
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

SOURCE = "https://studiumplus.de"
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".svg", ".webp", ".gif"}
REGISTRY_PATH = "registry.json"
SHARED_ASSETS_DIR = "_shared_assets"
COMMENT_TEMPLATE = "<!-- Cloned from: {source_url} at {timestamp} -->\n"
MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024
CSS_URL_PATTERN = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        parsed = urlparse(urljoin(SOURCE, url.strip()))
    path = parsed.path or "/"
    path = re.sub(r"/+", "/", path)
    if not path.endswith("/") and not posixpath.splitext(path)[1]:
        path += "/"
    return urlunparse(
        (parsed.scheme or "https", parsed.netloc or "studiumplus.de", path, "", "", "")
    )


def normalize_domain(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    return domain[4:] if domain.startswith("www.") else domain


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def page_dir_from_url(url: str, output_dir: Path) -> Path:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    return output_dir / path


def page_file_from_url(url: str, output_dir: Path) -> Path:
    return page_dir_from_url(url, output_dir) / "index.html"


def to_local_page_ref(current_page: Path, target_url: str, output_dir: Path) -> str:
    target_path = page_file_from_url(target_url, output_dir)
    rel = posixpath.relpath(
        target_path.as_posix(), start=current_page.parent.as_posix()
    )
    return rel


def is_internal_studiumplus(url: str) -> bool:
    domain = normalize_domain(url)
    return domain in {"studiumplus.de"}


def area_path_prefix(start_url: str) -> str:
    return urlparse(start_url).path


def in_area(url: str, prefix: str) -> bool:
    parsed = urlparse(url)
    return is_internal_studiumplus(url) and parsed.path.startswith(prefix)


def safe_filename_from_url(url: str, fallback_ext: str = ".bin") -> str:
    parsed = urlparse(url)
    base = posixpath.basename(parsed.path) or "asset"
    stem, ext = posixpath.splitext(base)
    if not ext:
        ext = fallback_ext
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{stem}-{digest}{ext}"


def download_binary(url: str) -> Optional[bytes]:
    req = Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; StudiumPlusClone/1.0)"}
    )
    try:
        with urlopen(req, timeout=30) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                logging.warning("Skip large asset (%s bytes): %s", content_length, url)
                return None
            chunks: List[bytes] = []
            total = 0
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    logging.warning(
                        "Skip oversized asset while reading (%s bytes): %s", total, url
                    )
                    return None
                chunks.append(chunk)
            return b"".join(chunks)
    except Exception:
        return None


def decode_text(binary: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return binary.decode(encoding)
        except UnicodeDecodeError:
            continue
    return binary.decode("utf-8", errors="replace")


def resolve_css_asset_url(css_url: str, raw_url: str) -> Optional[str]:
    candidate = raw_url.strip()
    lowered = candidate.lower()
    if not candidate:
        return None
    if lowered.startswith(("data:", "about:", "javascript:", "mailto:", "tel:")):
        return None
    if lowered.startswith("var("):
        return None
    if candidate.startswith(("#", "%23")):
        return None
    resolved = urljoin(css_url, candidate)
    return resolved if is_internal_studiumplus(resolved) else None


def rewrite_css(
    css_text: str,
    css_url: str,
    css_target: Path,
    shared_assets_dir: Path,
) -> str:
    resolved_cache: Dict[str, Optional[str]] = {}

    def replace_url(match: re.Match) -> str:
        quote = match.group(1) or ""
        raw_url = (match.group(2) or "").strip()
        resolved = resolve_css_asset_url(css_url, raw_url)
        if not resolved:
            return match.group(0)

        parsed = urlparse(resolved)
        cache_key = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, "")
        )
        local_ref = resolved_cache.get(cache_key)
        if local_ref is None:
            ext = posixpath.splitext(parsed.path)[1].lower()
            filename = safe_filename_from_url(cache_key, fallback_ext=ext or ".bin")
            target = shared_assets_dir / filename
            if not target.exists():
                binary = download_binary(cache_key)
                if not binary:
                    logging.warning("Failed CSS asset download: %s", cache_key)
                    resolved_cache[cache_key] = ""
                    return match.group(0)
                target.write_bytes(binary)

            local_ref = posixpath.relpath(
                target.as_posix(), start=css_target.parent.as_posix()
            )
            resolved_cache[cache_key] = local_ref

        if not local_ref:
            return match.group(0)

        fragment = urlparse(raw_url).fragment
        if fragment:
            local_ref = f"{local_ref}#{fragment}"
        return f"url({quote}{local_ref}{quote})"

    return CSS_URL_PATTERN.sub(replace_url, css_text)


def click_cookie_banner(page) -> None:
    labels = [
        "Alle akzeptieren",
        "Akzeptieren",
        "Zustimmen",
        "Einverstanden",
        "Nur notwendige",
        "Ablehnen",
        "Reject",
        "Accept",
    ]
    for label in labels:
        loc = page.get_by_role(
            "button", name=re.compile(re.escape(label), re.IGNORECASE)
        )
        try:
            if loc.count() > 0:
                loc.first.click(timeout=1200)
                page.wait_for_timeout(300)
                return
        except Exception:
            continue


def read_registry(path: Path) -> Dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"source": SOURCE, "last_updated": utc_now_iso(), "areas": []}


def write_registry(path: Path, registry: Dict) -> None:
    registry["last_updated"] = utc_now_iso()
    path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def collect_links(html: str, base_url: str) -> Iterable[str]:
    soup = BeautifulSoup(html, "lxml")
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if (
            not href
            or href.startswith("#")
            or href.startswith("mailto:")
            or href.startswith("tel:")
        ):
            continue
        absolute = normalize_url(urljoin(base_url, href))
        yield absolute


def rewrite_html(
    html: str,
    page_url: str,
    output_dir: Path,
    start_prefix: str,
    shared_assets_dir: Path,
) -> str:
    soup = BeautifulSoup(html, "lxml")
    page_file = page_file_from_url(page_url, output_dir)
    page_assets_dir = page_file.parent / "_assets"
    page_assets_dir.mkdir(parents=True, exist_ok=True)

    for img in soup.select("img"):
        candidates = [
            img.get("src"),
            img.get("data-src"),
            img.get("data-lazy-src"),
            img.get("srcset"),
        ]
        source_candidate = next((c for c in candidates if c), None)
        if not source_candidate:
            continue
        raw_url = source_candidate.split(",")[0].strip().split(" ")[0]
        resolved = urljoin(page_url, raw_url)
        if not is_internal_studiumplus(resolved):
            continue
        ext = posixpath.splitext(urlparse(resolved).path)[1].lower()
        if ext and ext not in SUPPORTED_IMAGE_EXTENSIONS:
            continue
        filename = safe_filename_from_url(resolved, fallback_ext=ext or ".jpg")
        target = page_assets_dir / filename
        if not target.exists():
            binary = download_binary(resolved)
            if binary:
                target.write_bytes(binary)
            else:
                logging.warning("Failed image download: %s", resolved)
                continue
        rel = posixpath.relpath(target.as_posix(), start=page_file.parent.as_posix())
        img["src"] = rel
        for attr in ("data-src", "data-lazy-src", "srcset"):
            if attr in img.attrs:
                img[attr] = rel

    for tag, attr, fallback_ext in (("link", "href", ".css"), ("script", "src", ".js")):
        # For link elements, restrict to stylesheet links to avoid rewriting non-stylesheet metadata links
        if tag == "link":
            selector = 'link[rel~="stylesheet"][href]'
        else:
            selector = f"{tag}[{attr}]"
        for el in soup.select(selector):
            src = (el.get(attr) or "").strip()
            if not src:
                continue
            resolved = urljoin(page_url, src)
            if not is_internal_studiumplus(resolved):
                continue
            filename = safe_filename_from_url(resolved, fallback_ext=fallback_ext)
            target = shared_assets_dir / filename

            if tag == "link":
                binary = download_binary(resolved)
                if binary:
                    css_text = decode_text(binary)
                    rewritten_css = rewrite_css(
                        css_text, resolved, target, shared_assets_dir
                    )
                    target.write_text(rewritten_css, encoding="utf-8")
                elif not target.exists():
                    logging.warning("Failed shared asset download: %s", resolved)
                    continue
            elif not target.exists():
                binary = download_binary(resolved)
                if not binary:
                    logging.warning("Failed shared asset download: %s", resolved)
                    continue
                target.write_bytes(binary)
            rel = posixpath.relpath(
                target.as_posix(), start=page_file.parent.as_posix()
            )
            el[attr] = rel

    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if (
            not href
            or href.startswith("#")
            or href.startswith("mailto:")
            or href.startswith("tel:")
        ):
            continue
        resolved = normalize_url(urljoin(page_url, href))
        if in_area(resolved, start_prefix):
            a["href"] = to_local_page_ref(page_file, resolved, output_dir)
        elif is_internal_studiumplus(resolved):
            a["href"] = resolved
        else:
            a["href"] = urljoin(page_url, href)

    header = COMMENT_TEMPLATE.format(source_url=page_url, timestamp=utc_now_iso())
    return header + str(soup)


def extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    return title or "Ohne Titel"


def slug_from_path(path: str) -> str:
    clean = path.rstrip("/").split("/")
    return clean[-1] if clean and clean[-1] else "root"


def crawl_area(
    browser,
    start_url: str,
    output_dir: Path,
    max_depth: int,
    delay: float,
    thumbnails_dir: Path,
) -> Dict:
    start_url = normalize_url(start_url)
    prefix = area_path_prefix(start_url)
    area_dir = page_dir_from_url(start_url, output_dir)
    area_dir.mkdir(parents=True, exist_ok=True)
    shared_assets_dir = output_dir / SHARED_ASSETS_DIR
    shared_assets_dir.mkdir(parents=True, exist_ok=True)

    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()

    queue: deque[Tuple[str, int]] = deque([(start_url, 0)])
    visited: Set[str] = set()
    pages: List[Dict] = []

    while queue:
        current_url, depth = queue.popleft()
        if current_url in visited or depth > max_depth:
            continue
        visited.add(current_url)

        try:
            response = page.goto(current_url, wait_until="networkidle", timeout=45000)
            if response and response.status >= 400:
                logging.warning(
                    "Skip %s due to status %s", current_url, response.status
                )
                continue
            click_cookie_banner(page)
            page.wait_for_timeout(500)
            html = page.content()
        except PlaywrightTimeoutError:
            logging.error("Timeout while loading %s", current_url)
            continue
        except Exception:
            logging.exception("Failed to load %s", current_url)
            continue

        if current_url == start_url:
            thumb_name = f"{slug_from_path(prefix)}.png"
            thumb_target = thumbnails_dir / thumb_name
            thumbnails_dir.mkdir(parents=True, exist_ok=True)
            try:
                page.screenshot(path=str(thumb_target), full_page=False)
            except Exception:
                logging.warning("Could not create thumbnail for %s", current_url)

        rewritten = rewrite_html(
            html, current_url, output_dir, prefix, shared_assets_dir
        )
        target_file = page_file_from_url(current_url, output_dir)
        ensure_parent(target_file)
        target_file.write_text(rewritten, encoding="utf-8")

        pages.append(
            {
                "source_url": current_url,
                "local_path": target_file.relative_to(output_dir).as_posix(),
                "title": extract_title(html),
            }
        )

        for link in collect_links(html, current_url):
            if in_area(link, prefix) and link not in visited:
                queue.append((link, depth + 1))

        if delay > 0:
            time.sleep(delay)

    context.close()

    slug = slug_from_path(prefix)
    first_title = pages[0]["title"] if pages else slug.replace("-", " ").title()
    return {
        "id": slug,
        "label": first_title,
        "source_url": start_url,
        "local_path": f"{prefix.strip('/')}/" if prefix.strip("/") else "",
        "thumbnail": f"thumbnails/{slug}.png",
        "cloned_at": utc_now_iso(),
        "pages_count": len(pages),
        "pages": pages,
    }


def upsert_area(registry: Dict, area: Dict) -> None:
    areas = registry.setdefault("areas", [])
    for idx, existing in enumerate(areas):
        if existing.get("source_url") == area.get("source_url"):
            areas[idx] = area
            return
    areas.append(area)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Partieller StudiumPlus-Klon mit Playwright"
    )
    parser.add_argument("urls", nargs="+", help="Start-URLs der zu klonenden Bereiche")
    parser.add_argument("--max-depth", type=int, default=5, help="Maximale Crawl-Tiefe")
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Wartezeit zwischen Seiten in Sekunden"
    )
    parser.add_argument("--output-dir", default=".", help="Ausgabeordner")
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir).resolve()
    registry_path = output_dir / REGISTRY_PATH
    log_path = output_dir / "scripts" / "clone.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    registry = read_registry(registry_path)
    thumbnails_dir = output_dir / "thumbnails"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for raw_url in args.urls:
                start_url = normalize_url(raw_url)
                logging.info("Cloning area: %s", start_url)
                area = crawl_area(
                    browser,
                    start_url,
                    output_dir,
                    args.max_depth,
                    args.delay,
                    thumbnails_dir,
                )
                upsert_area(registry, area)
        finally:
            browser.close()

    write_registry(registry_path, registry)
    logging.info("Done. Registry updated: %s", registry_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
