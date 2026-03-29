"""
ai_engine/scraper.py — Wrapper module for the root-level scraper.

Provides a `scrape_url` function for use by Django views.
"""

import os
import sys
import requests
from bs4 import BeautifulSoup


# ── Configuration ───────────────────────────────────────────────────
ALLOWED_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6"}
STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 15  # seconds


def fetch_page(url: str) -> str:
    """Download the raw HTML for *url*."""
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=False)
    response.raise_for_status()
    return response.text


def extract_clean_text(html: str) -> str:
    """Return only the meaningful text from *html*."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    lines: list[str] = []
    for tag in soup.find_all(ALLOWED_TAGS):
        text = tag.get_text(separator=" ", strip=True)
        if text:
            lines.append(text)

    return "\n\n".join(lines)


def scrape_url(url: str) -> str:
    """High-level API: fetch a URL and return cleaned text.

    This is the function called by Django views.
    """
    print(f"[scraper] Fetching: {url}")
    html = fetch_page(url)
    print(f"[scraper] Parsing HTML ({len(html):,} bytes)...")
    text = extract_clean_text(html)
    print(f"[scraper] Extracted {len(text):,} characters of clean text")
    return text
