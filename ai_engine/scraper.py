"""
ai_engine/scraper.py — Wrapper module for the root-level scraper.

Provides a `scrape_url` function for use by Django views.
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# ── Configuration ───────────────────────────────────────────────────
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
    response.encoding = 'utf-8'  # Force UTF-8 to prevent Â£ encoding errors
    response.raise_for_status()
    return response.text


def extract_clean_text(html: str) -> str:
    """Return structured Markdown-style text for 100% of the page."""
    soup = BeautifulSoup(html, "html.parser")

    # Strictly non-visible tags
    STRIP_TAGS = {"script", "style", "noscript"}
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    body = soup.find("body")
    if not body:
        return ""

    markdown_buffer = []

    # 1. Structured Feature: Header
    markdown_buffer.append("# WEBSITE CONTENT\n")

    # 2. Structured Feature: Sidebar Categories
    categories = soup.select("div.side_categories ul li a")
    if categories:
        markdown_buffer.append("## BOOK CATEGORIES")
        for cat in categories:
            name = cat.get_text(strip=True)
            markdown_buffer.append(f"* Category: {name}")
        markdown_buffer.append("\n")

    # 3. Structured Feature: Product Pods
    products = soup.select("article.product_pod")
    if products:
        markdown_buffer.append("## PRODUCT DATA")
        for pod in products:
            title = pod.h3.a["title"] if pod.h3 and pod.h3.a else pod.h3.get_text(strip=True)
            price = pod.select_one("p.price_color").get_text(strip=True) if pod.select_one("p.price_color") else "N/A"
            
            # Star Rating Detection
            rating = "Unknown"
            rating_tag = pod.select_one("p.star-rating")
            if rating_tag:
                classes = rating_tag.get("class", [])
                for cls in ["One", "Two", "Three", "Four", "Five"]:
                    if cls in classes:
                        rating = f"{cls} stars"

            markdown_buffer.append(f"### Product: {title} | Price: {price} | Rating: {rating}")
        markdown_buffer.append("\n")

    # 4. Fallback: Catch-all for landing pages
    # We still fetch everything else to satisfy the 'all tags' request
    general_text = body.get_text(separator="\n", strip=True)
    if products or categories:
        # If we already extracted products/categories, add a separator for the rest
        markdown_buffer.append("## RAW PAGE TEXT CONTENT")
    
    markdown_buffer.append(general_text)

    # Final cleanup
    full_text = "\n".join(markdown_buffer)
    full_text = full_text.replace('Â£', '£').replace('Â', '')
    
    return full_text


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


def scrape_url(url: str) -> tuple[str, set[str]]:
    """High-level API: fetch a URL and return cleaned text and internal links.

    This is the function called by Django views and tasks.
    Returns:
        tuple: (extracted_text, set_of_internal_links)
    """
    print(f"[scraper] Fetching: {url}")
    html = fetch_page(url)
    print(f"[scraper] Parsing HTML ({len(html):,} bytes)...")
    
    text = extract_clean_text(html)
    links = find_internal_links(html, url)
    
    print(f"[scraper] Extracted {len(text):,} characters of clean text and {len(links)} internal links")
    return text, links
