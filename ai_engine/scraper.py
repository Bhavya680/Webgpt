"""
ai_engine/scraper.py — Universal web scraper.

Provides `scrape_url()` for use by Django views and Celery tasks.
Now powered by the Heuristic Detection Engine for site-agnostic
content extraction.
"""

import warnings
import urllib3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from .heuristic_engine import build_semantic_markdown

# Suppress insecure request warnings caused by verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


# ── Configuration ───────────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

REQUEST_TIMEOUT = 15  # seconds


def fetch_page(url: str, session: requests.Session = None) -> str:
    """Download the raw HTML for *url* using an optional session."""
    
    # Add a pseudo-Referer based on the base domain to bypass strict anti-leeching
    parsed = urlparse(url)
    custom_headers = HEADERS.copy()
    custom_headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"

    req_func = session.get if session else requests.get
    
    response = req_func(url, headers=custom_headers, timeout=REQUEST_TIMEOUT, verify=False)
    response.encoding = 'utf-8'
    response.raise_for_status()
    return response.text


def find_internal_links(html: str, base_url: str) -> set[str]:
    """Extract all valid internal hrefs from the given HTML."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    base_domain = urlparse(base_url).netloc

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        # Resolve to absolute URL
        absolute_url = urljoin(base_url, href)
        parsed_url = urlparse(absolute_url)

        # Only keep links from the same domain
        if parsed_url.netloc == base_domain and parsed_url.scheme in ('http', 'https'):
            # Strip fragments for deduping
            clean_url = parsed_url._replace(fragment="").geturl()
            links.add(clean_url)

    return links


def scrape_url(url: str, session: requests.Session = None) -> tuple[str, set[str]]:
    """High-level API: fetch a URL and return cleaned text and internal links.

    This is the function called by Django views and tasks.
    Returns:
        tuple: (semantic_markdown_text, set_of_internal_links)
    """
    print(f"[scraper] Fetching: {url}")
    html = fetch_page(url, session=session)
    print(f"[scraper] Parsing HTML ({len(html):,} bytes)...")

    # Use the Universal Heuristic Engine for content extraction
    text = build_semantic_markdown(html, url)
    links = find_internal_links(html, url)

    print(f"[scraper] Extracted {len(text):,} characters of semantic markdown and {len(links)} internal links")
    return text, links
