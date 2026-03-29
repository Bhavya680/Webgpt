"""
scraper.py — Core web scraper for WebGPT.

Fetches a target URL, extracts clean text from <p> and heading tags
(<h1>–<h6>), strips scripts/nav/footer cruft, and saves the result
to data/scraped.txt.

Usage:
    python scraper.py <URL>

Example:
    python scraper.py https://en.wikipedia.org/wiki/Python_(programming_language)
"""

import sys
import os
import requests
from bs4 import BeautifulSoup


# ── Configuration ───────────────────────────────────────────────────
ALLOWED_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6"}
STRIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript"}
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "scraped.txt")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 15  # seconds


# ── Core functions ──────────────────────────────────────────────────
def fetch_page(url: str) -> str:
    """Download the raw HTML for *url*.

    Raises
    ------
    requests.HTTPError
        If the server responds with a non-2xx status code.
    requests.ConnectionError
        If the server is unreachable.
    """
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def extract_clean_text(html: str) -> str:
    """Return only the meaningful text from *html*.

    Steps:
    1.  Remove all <script>, <style>, <nav>, <footer>, <header>,
        <aside>, <form>, and <noscript> subtrees so their inner text
        never leaks into the output.
    2.  Select only <p> and <h1>–<h6> elements.
    3.  Collapse whitespace and drop empty lines.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Strip noise subtrees first
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    # 2. Gather text from allowed tags only
    lines: list[str] = []
    for tag in soup.find_all(ALLOWED_TAGS):
        text = tag.get_text(separator=" ", strip=True)
        if text:
            lines.append(text)

    return "\n\n".join(lines)


def save_text(text: str, path: str) -> None:
    """Persist *text* to *path*, creating parent directories as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def scrape(url: str) -> str:
    """High-level API: fetch → extract → save → return cleaned text."""
    print(f"[*] Fetching: {url}")
    html = fetch_page(url)
    print(f"[*] Parsing HTML ({len(html):,} bytes)...")
    text = extract_clean_text(html)
    save_text(text, OUTPUT_FILE)
    print(f"[*] Saved cleaned text to {OUTPUT_FILE}")
    return text


# ── CLI entry point ─────────────────────────────────────────────────
def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <URL>")
        print("Example: python scraper.py https://example.com")
        sys.exit(1)

    url = sys.argv[1]

    try:
        text = scrape(url)
    except requests.ConnectionError:
        print(f"[!] Could not connect to {url}. Check the URL and your network.")
        sys.exit(1)
    except requests.HTTPError as exc:
        print(f"[!] HTTP error: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"[!] Unexpected error: {exc}")
        sys.exit(1)

    # Print to terminal
    print("\n" + "=" * 72)
    print("  SCRAPED TEXT")
    print("=" * 72 + "\n")
    print(text)


if __name__ == "__main__":
    main()
