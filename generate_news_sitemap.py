#!/usr/bin/env python3
import html
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

SITE_URL = os.getenv("SITE_URL", "https://albanyantree.com").rstrip("/")
SITEMAP_URL = os.getenv("SITEMAP_URL", f"{SITE_URL}/sitemap.xml")
PUBLICATION_NAME = os.getenv("PUBLICATION_NAME", "Albany & Tree")
PUBLICATION_LANGUAGE = os.getenv("PUBLICATION_LANGUAGE", "en")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "news-sitemap.xml")
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "48"))
MAX_URLS = min(int(os.getenv("MAX_URLS", "1000")), 1000)

DEFAULT_PATTERNS = [r"/insights/.+"]
PATTERNS = [
    p.strip()
    for p in os.getenv("NEWS_URL_PATTERNS", ",".join(DEFAULT_PATTERNS)).split(",")
    if p.strip()
]
COMPILED_PATTERNS = [re.compile(p) for p in PATTERNS]


def fetch_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; NewsSitemapBot/1.0; +https://albanyantree.com)"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def should_include_url(url: str) -> bool:
    return any(p.search(url) for p in COMPILED_PATTERNS)


def extract_title(page_html: str) -> Optional[str]:
    m = re.search(r"<title[^>]*>(.*?)</title>", page_html, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    title = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()
    title = re.sub(r"\s*[|\-–—]\s*Albany\s*&\s*Tree\s*$", "", title, flags=re.IGNORECASE)
    return title or None


def read_candidates() -> List[Tuple[str, datetime]]:
    xml_text = fetch_text(SITEMAP_URL)
    root = ET.fromstring(xml_text)

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    candidates: List[Tuple[str, datetime]] = []
    threshold = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)

    for url_node in root.findall("sm:url", ns):
        loc = url_node.findtext("sm:loc", default="", namespaces=ns).strip()
        lastmod_raw = url_node.findtext("sm:lastmod", default="", namespaces=ns)
        lastmod = parse_iso_datetime(lastmod_raw)

        if not loc or not lastmod:
            continue
        if not should_include_url(loc):
            continue
        if lastmod < threshold:
            continue

        candidates.append((loc, lastmod))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:MAX_URLS]


def build_news_sitemap(entries: List[Tuple[str, datetime, str]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
    ]

    for loc, pub_date, title in entries:
        lines.extend(
            [
                "  <url>",
                f"    <loc>{html.escape(loc, quote=True)}</loc>",
                "    <news:news>",
                "      <news:publication>",
                f"        <news:name>{html.escape(PUBLICATION_NAME)}</news:name>",
                f"        <news:language>{html.escape(PUBLICATION_LANGUAGE)}</news:language>",
                "      </news:publication>",
                f"      <news:publication_date>{pub_date.strftime('%Y-%m-%dT%H:%M:%SZ')}</news:publication_date>",
                f"      <news:title>{html.escape(title)}</news:title>",
                "    </news:news>",
                "  </url>",
            ]
        )

    lines.append("</urlset>")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    try:
        candidates = read_candidates()
    except Exception as e:
        print(f"Failed to read sitemap: {e}", file=sys.stderr)
        return 1

    entries: List[Tuple[str, datetime, str]] = []
    for loc, pub_date in candidates:
        try:
            page_html = fetch_text(loc)
            title = extract_title(page_html)
            if not title:
                print(f"Skip (title not found): {loc}")
                continue
            entries.append((loc, pub_date, title))
            print(f"Include: {loc}")
        except Exception as e:
            print(f"Skip (fetch error): {loc} -> {e}")

    xml_out = build_news_sitemap(entries)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(xml_out)

    print(f"Written {OUTPUT_PATH} with {len(entries)} URLs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
