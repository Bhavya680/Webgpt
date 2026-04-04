"""
ai_engine/heuristic_engine.py — Universal Heuristic Scraper Engine

Four-stage pattern-recognition pipeline that converts raw HTML into
Semantic Markdown without any site-specific CSS selectors.

Stages:
  1. Navigation Detection  → [NAVIGATION_MENU]
  2. Grid Recognition       → [PRODUCT_GRID] / [CONTENT_GRID]
  3. Price Extraction        → [PRICE] / ### ITEM POINT
  4. CTA Mapping             → [ACTION_BUTTON]

Plus: Table extraction, page metadata, hero text, breadcrumbs, footer.
"""

import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag


# ══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════

# Price regex — covers £, $, €, ¥, ₹ and text-prefix currencies
PRICE_REGEX = re.compile(
    r'([£$€¥₹]\s?\d{1,6}(?:[,.\s]?\d{3})*(?:[.,]\d{1,2})?)',
    re.UNICODE
)
PRICE_TEXT_REGEX = re.compile(
    r'((?:USD|EUR|GBP|INR|AUD|CAD|JPY|CNY)\s?\d{1,6}(?:[,.\s]?\d{3})*(?:[.,]\d{1,2})?)',
    re.IGNORECASE
)

# CTA keyword dictionary with weights
CTA_KEYWORDS = {
    'purchase': {
        'keywords': ['buy', 'add to cart', 'add to bag', 'add to basket',
                     'purchase', 'order now', 'checkout', 'shop now'],
        'weight': 10,
    },
    'signup': {
        'keywords': ['sign up', 'register', 'create account', 'join',
                     'get started', 'start free trial', 'subscribe',
                     'start trial', 'try free'],
        'weight': 9,
    },
    'contact': {
        'keywords': ['contact us', 'get in touch', 'request a quote',
                     'book a call', 'schedule', 'enquire', 'book a demo'],
        'weight': 8,
    },
    'download': {
        'keywords': ['download', 'get the app', 'install', 'free download'],
        'weight': 7,
    },
    'info': {
        'keywords': ['learn more', 'read more', 'view details', 'see more',
                     'explore', 'discover', 'find out'],
        'weight': 6,
    },
    'social': {
        'keywords': ['share', 'tweet', 'pin it', 'follow us'],
        'weight': 3,
    },
}

# Tags to completely strip from the DOM before analysis
NOISE_TAGS = {'script', 'style', 'noscript', 'svg', 'iframe'}

# Exclusion class patterns for navigation false-positive filtering
NAV_EXCLUDE_PATTERNS = ['footer', 'breadcrumb', 'social', 'share',
                        'cookie', 'banner', 'modal', 'popup']

# Maximum output length (characters)
MAX_OUTPUT_LENGTH = 15000


# ══════════════════════════════════════════════════════════════════════
# STAGE 1: NAVIGATION DETECTION
# ══════════════════════════════════════════════════════════════════════

def detect_navigation(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """
    Detect navigation menus using the Navigation Confidence Score (NCS).

    NCS = (NAV_TAG × 30) + (LIST_DENSITY × 25) + (LINK_COUNT × 20)
        + (POSITION_HINT × 15) + (ARIA_ROLE × 10)

    Acceptance threshold: NCS ≥ 50 (graceful degradation to 35).
    """
    base_domain = urlparse(base_url).netloc
    candidates = []

    # Collect candidate containers: <nav>, <ul>, <ol>
    for element in soup.find_all(['nav', 'ul', 'ol']):
        # Skip if inside excluded containers
        parent_classes = ' '.join(element.get('class', []))
        if any(excl in parent_classes.lower() for excl in NAV_EXCLUDE_PATTERNS):
            continue

        # Also check parent elements for exclusion patterns
        skip = False
        for parent in element.parents:
            if isinstance(parent, Tag):
                parent_cls = ' '.join(parent.get('class', []))
                if any(excl in parent_cls.lower() for excl in ['footer']):
                    skip = True
                    break
        if skip:
            continue

        anchors = element.find_all('a', href=True)
        if not anchors:
            continue

        total_links = len(anchors)
        internal_links = sum(
            1 for a in anchors
            if urlparse(urljoin(base_url, a['href'])).netloc == base_domain
        )

        # Compute NCS factors
        is_nav_tag = 1 if element.name == 'nav' else 0
        list_density = 1 if total_links >= 3 else 0
        link_count = 1 if internal_links >= 5 else 0
        # Position hint: approximate by element's position in DOM order
        all_elements = list(soup.body.children) if soup.body else []
        body_children = [c for c in all_elements if isinstance(c, Tag)]
        position_hint = 0
        if body_children:
            for idx, child in enumerate(body_children):
                if element == child or element in child.descendants:
                    position_hint = 1 if idx < len(body_children) * 0.35 else 0
                    break
        # ARIA/Role check
        aria_role = 0
        role = element.get('role', '')
        aria_label = element.get('aria-label', '')
        if any(kw in (role + aria_label).lower() for kw in ['navigation', 'nav', 'menu']):
            aria_role = 1

        ncs = (is_nav_tag * 30) + (list_density * 25) + (link_count * 20) \
            + (position_hint * 15) + (aria_role * 10)

        if ncs >= 50:
            items = []
            for a in anchors:
                text = a.get_text(strip=True)
                href = a.get('href', '')
                if text and len(text) < 60:
                    items.append({'text': text, 'href': href})
            if items:
                candidates.append({'ncs': ncs, 'items': items})

    # Graceful degradation: if nothing passed 50, lower to 35
    if not candidates:
        for element in soup.find_all(['nav', 'ul', 'ol']):
            anchors = element.find_all('a', href=True)
            if len(anchors) >= 3:
                items = []
                for a in anchors:
                    text = a.get_text(strip=True)
                    href = a.get('href', '')
                    if text and len(text) < 60:
                        items.append({'text': text, 'href': href})
                if items:
                    candidates.append({'ncs': 35, 'items': items})
                    break

    # Deduplicate by item text (some pages have desktop + mobile navs)
    seen_texts = set()
    deduplicated = []
    for nav in candidates:
        key = tuple(item['text'] for item in nav['items'][:5])
        if key not in seen_texts:
            seen_texts.add(key)
            deduplicated.append(nav)

    return deduplicated


# ══════════════════════════════════════════════════════════════════════
# STAGE 2: PRICE EXTRACTION
# ══════════════════════════════════════════════════════════════════════

def extract_prices(soup: BeautifulSoup) -> list[dict]:
    """
    Two-pass price detection:
      Pass A — Global regex scan for currency patterns.
      Pass B — DOM walk-up to group price with its product context.
    """
    items = []
    body = soup.find('body')
    if not body:
        return items

    seen_prices = set()

    # Pass A: Find all text nodes containing price patterns
    for text_node in body.find_all(string=True):
        text = str(text_node).strip()
        if not text:
            continue

        matches = PRICE_REGEX.findall(text)
        matches += PRICE_TEXT_REGEX.findall(text)

        for price_str in matches:
            price_str = price_str.strip()
            if price_str in seen_prices:
                continue
            seen_prices.add(price_str)

            # Pass B: Walk up to find item container
            parent = text_node.parent
            item = _extract_item_context(parent, price_str)
            if item:
                items.append(item)

    return items


def _extract_item_context(element: Tag, price_str: str) -> dict | None:
    """Walk up the DOM from a price match to find the Item Container."""
    block_tags = {'div', 'article', 'section', 'li', 'td', 'tr', 'main'}
    container = element

    # Walk up to first block-level ancestor
    depth = 0
    while container and depth < 6:
        if isinstance(container, Tag) and container.name in block_tags:
            break
        container = container.parent
        depth += 1

    if not container or not isinstance(container, Tag):
        return None

    # Extract title: first heading, strong, or anchor text
    title = ''
    for tag in container.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'a']):
        t = tag.get_text(strip=True)
        if t and len(t) > 2 and t != price_str:
            title = t[:150]
            break

    # Extract image
    img = container.find('img')
    image_src = ''
    if img:
        image_src = img.get('src', '') or img.get('data-src', '')

    # Extract description
    desc = ''
    for p in container.find_all('p'):
        t = p.get_text(strip=True)
        if t and len(t) > 20 and t != price_str:
            desc = t[:200]
            break

    return {
        'title': title,
        'price': price_str,
        'image': image_src,
        'description': desc,
    }


# ══════════════════════════════════════════════════════════════════════
# STAGE 3: GRID RECOGNITION (Sibling Similarity Index)
# ══════════════════════════════════════════════════════════════════════

def detect_grid(soup: BeautifulSoup) -> list[dict]:
    """
    Detect repeating visual structures using Jaccard similarity
    of CSS class-names across sibling elements.
    """
    grids = []
    body = soup.find('body')
    if not body:
        return grids

    # Scan elements for grid candidate parents
    scan_tags = {'div', 'section', 'ul', 'ol', 'main', 'article', 'tbody'}
    for parent in body.find_all(scan_tags):
        children = [c for c in parent.children if isinstance(c, Tag)]
        if len(children) < 3:
            continue

        # Group children by tag name
        tag_groups = {}
        for child in children:
            tag_groups.setdefault(child.name, []).append(child)

        for tag_name, group in tag_groups.items():
            if len(group) < 3:
                continue

            # Compute Jaccard similarity across class-name sets
            class_sets = [set(child.get('class', [])) for child in group]
            # Filter out empty class sets
            non_empty = [cs for cs in class_sets if cs]
            if not non_empty:
                # Even without classes, if all same tag with ≥3, treat as grid
                ssi = 0.5 if len(group) >= 5 else 0.3
            else:
                ssi = _mean_jaccard(non_empty)

            if ssi < 0.40:
                continue

            # Classify the grid type
            has_prices = sum(1 for g in group if PRICE_REGEX.search(g.get_text()))
            has_times = sum(1 for g in group if g.find('time'))
            has_images = sum(1 for g in group if g.find('img'))

            grid_type = 'CONTENT_GRID'
            if has_prices / len(group) >= 0.5:
                grid_type = 'PRODUCT_GRID'
            elif has_times / len(group) >= 0.5:
                grid_type = 'ARTICLE_GRID'
            elif has_images / len(group) >= 0.8:
                grid_type = 'IMAGE_GALLERY'

            confidence = 'high' if ssi >= 0.70 else 'medium'

            grid_items = []
            for child in group:
                item = _extract_grid_item(child)
                if item:
                    grid_items.append(item)

            if grid_items:
                grids.append({
                    'type': grid_type,
                    'confidence': confidence,
                    'count': len(grid_items),
                    'items': grid_items,
                })

    return grids


def _extract_grid_item(element: Tag) -> dict | None:
    """Extract structured data from a single grid cell."""
    text = element.get_text(strip=True)
    if not text or len(text) < 3:
        return None

    # Title: first heading or strong or anchor
    title = ''
    for tag in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'a']):
        t = tag.get_text(strip=True)
        if t and len(t) > 2:
            title = t[:150]
            break
    if not title:
        title = text[:80]

    # Price
    price = ''
    price_match = PRICE_REGEX.search(text)
    if price_match:
        price = price_match.group(0).strip()
    else:
        price_text_match = PRICE_TEXT_REGEX.search(text)
        if price_text_match:
            price = price_text_match.group(0).strip()

    # Image
    img = element.find('img')
    image = (img.get('src', '') or img.get('data-src', '')) if img else ''

    # Description
    desc = ''
    for p in element.find_all('p'):
        t = p.get_text(strip=True)
        if t and len(t) > 15:
            desc = t[:200]
            break

    # Link
    link = ''
    a = element.find('a', href=True)
    if a:
        link = a.get('href', '')

    return {
        'title': title,
        'price': price,
        'image': image,
        'description': desc,
        'link': link,
    }


def _mean_jaccard(class_sets: list[set]) -> float:
    """Compute mean pairwise Jaccard similarity."""
    if len(class_sets) < 2:
        return 0.0

    total = 0.0
    count = 0
    for i in range(len(class_sets)):
        for j in range(i + 1, len(class_sets)):
            a, b = class_sets[i], class_sets[j]
            union = a | b
            if union:
                total += len(a & b) / len(union)
            count += 1

    return total / count if count else 0.0


# ══════════════════════════════════════════════════════════════════════
# STAGE 4: CTA BUTTON MAPPING
# ══════════════════════════════════════════════════════════════════════

def map_cta(soup: BeautifulSoup) -> list[dict]:
    """
    Detect call-to-action elements via keyword matching + class fallback.
    """
    cta_elements = []
    seen = set()

    for element in soup.find_all(['button', 'a', 'input']):
        # Get visible text
        if element.name == 'input':
            text = element.get('value', '')
        else:
            text = element.get_text(strip=True)

        if not text or len(text) > 80:
            continue

        # Also check aria-label
        aria = element.get('aria-label', '')
        search_text = (text + ' ' + aria).lower()

        # Skip if already seen
        href = element.get('href', '#')
        dedup_key = f"{text}|{href}"
        if dedup_key in seen:
            continue

        # Check keyword matches
        best_category = None
        best_weight = 0
        for category, config in CTA_KEYWORDS.items():
            for kw in config['keywords']:
                if kw in search_text:
                    if config['weight'] > best_weight:
                        best_weight = config['weight']
                        best_category = category
                    break

        # Class-name fallback for styled <a> tags
        if not best_category:
            classes = ' '.join(element.get('class', []))
            if any(btn_cls in classes.lower() for btn_cls in ['btn', 'button', 'cta', 'action']):
                if element.name == 'a' and href and href != '#':
                    best_category = 'info'
                    best_weight = 4

        if best_category:
            seen.add(dedup_key)
            cta_elements.append({
                'label': text,
                'href': href or '#',
                'category': best_category,
                'weight': best_weight,
            })

    return cta_elements


# ══════════════════════════════════════════════════════════════════════
# TABLE EXTRACTION (Universal)
# ══════════════════════════════════════════════════════════════════════

def extract_tables(soup: BeautifulSoup) -> list[dict]:
    """
    Convert HTML <table> elements into structured markdown tables.
    Works for any website: data tables, comparison tables, stats, etc.
    """
    tables = []
    for table in soup.find_all('table'):
        headers = []
        rows = []

        # Extract headers from <thead> or first <tr>
        thead = table.find('thead')
        if thead:
            for th in thead.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))
        else:
            first_tr = table.find('tr')
            if first_tr:
                ths = first_tr.find_all('th')
                if ths:
                    headers = [th.get_text(strip=True) for th in ths]

        # Extract data rows from <tbody> or all <tr>
        tbody = table.find('tbody') or table
        for tr in tbody.find_all('tr'):
            cells = tr.find_all(['td', 'th'])
            if not cells:
                continue
            row = [cell.get_text(strip=True) for cell in cells]
            # Skip header row if already captured
            if row == headers:
                continue
            if any(cell for cell in row):
                rows.append(row)

        if rows:
            # Get a caption/title for the table if available
            caption = ''
            caption_tag = table.find('caption')
            if caption_tag:
                caption = caption_tag.get_text(strip=True)
            else:
                # Check preceding heading
                prev = table.find_previous_sibling(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if prev:
                    caption = prev.get_text(strip=True)

            tables.append({
                'caption': caption,
                'headers': headers,
                'rows': rows[:100],  # Cap at 100 rows per table
            })

    return tables


# ══════════════════════════════════════════════════════════════════════
# PAGE METADATA EXTRACTION
# ══════════════════════════════════════════════════════════════════════

def extract_page_metadata(soup: BeautifulSoup) -> dict:
    """Extract page title, meta description, hero text, breadcrumbs."""
    metadata = {}

    # Page title
    title_tag = soup.find('title')
    h1_tag = soup.find('h1')
    metadata['page_title'] = ''
    if title_tag:
        metadata['page_title'] = title_tag.get_text(strip=True)
    elif h1_tag:
        metadata['page_title'] = h1_tag.get_text(strip=True)

    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    og_desc = soup.find('meta', attrs={'property': 'og:description'})
    metadata['meta_description'] = ''
    if meta_desc and meta_desc.get('content'):
        metadata['meta_description'] = meta_desc['content'].strip()[:300]
    elif og_desc and og_desc.get('content'):
        metadata['meta_description'] = og_desc['content'].strip()[:300]

    # Hero text: large headings in the top portion of the page
    metadata['hero_text'] = ''
    body = soup.find('body')
    if body:
        body_children = [c for c in body.children if isinstance(c, Tag)]
        top_section = body_children[:max(3, len(body_children) // 4)]
        for section in top_section:
            for heading in section.find_all(['h1', 'h2']):
                text = heading.get_text(strip=True)
                if text and len(text) > 10 and text != metadata['page_title']:
                    metadata['hero_text'] = text[:200]
                    break
            if metadata['hero_text']:
                break

    # Breadcrumbs
    metadata['breadcrumb'] = ''
    breadcrumb_el = soup.find(attrs={'class': lambda c: c and 'breadcrumb' in str(c).lower()})
    if not breadcrumb_el:
        breadcrumb_el = soup.find(attrs={'aria-label': lambda v: v and 'breadcrumb' in v.lower()})
    if breadcrumb_el:
        items = [a.get_text(strip=True) for a in breadcrumb_el.find_all('a')]
        # Also get non-link breadcrumb items
        for span in breadcrumb_el.find_all(['span', 'li']):
            t = span.get_text(strip=True)
            if t and t not in items and len(t) < 50:
                items.append(t)
        metadata['breadcrumb'] = ' > '.join(items[:8])

    # Footer links
    metadata['footer_links'] = []
    footer = soup.find('footer')
    if footer:
        for a in footer.find_all('a', href=True)[:20]:
            text = a.get_text(strip=True)
            if text and len(text) < 50:
                metadata['footer_links'].append({
                    'text': text,
                    'href': a['href']
                })

    return metadata


# ══════════════════════════════════════════════════════════════════════
# SEMANTIC MARKDOWN SERIALIZER
# ══════════════════════════════════════════════════════════════════════

def _serialize_navigation(nav_blocks: list[dict]) -> str:
    """Serialize navigation blocks to simplified Semantic Markdown."""
    lines = []
    for nav in nav_blocks:
        lines.append('[SITE_NAVIGATION]')
        # Filter and joined items for token efficiency
        nav_items = [f"{item['text']}" for item in nav['items'][:20]]
        lines.append(" | ".join(nav_items))
        lines.append('[/SITE_NAVIGATION]')
        lines.append('')
    return '\n'.join(lines)


def _serialize_grids(grids: list[dict]) -> str:
    """Serialize detected grids to Semantic Markdown."""
    lines = []
    for grid in grids:
        lines.append(f"[{grid['type']}] ({grid['count']} items detected)")
        lines.append('')
        for item in grid['items'][:50]:  # Cap at 50 items per grid
            lines.append('### ITEM POINT')
            if item['title']:
                lines.append(f"Title: {item['title']}")
            if item['price']:
                lines.append(f"[PRICE] {item['price']} [/PRICE]")
            if item['image']:
                lines.append(f"Image: {item['image']}")
            if item['description']:
                lines.append(f"Description: {item['description']}")
            if item['link']:
                lines.append(f"Link: {item['link']}")
            lines.append('---')
        lines.append(f"[/{grid['type']}]")
        lines.append('')
    return '\n'.join(lines)


def _serialize_prices(price_items: list[dict], grid_titles: set) -> str:
    """Serialize standalone price items (not already in a grid)."""
    lines = []
    for item in price_items:
        # Skip items already captured by grid detection
        if item['title'] and item['title'] in grid_titles:
            continue
        lines.append('### ITEM POINT')
        if item['title']:
            lines.append(f"Title: {item['title']}")
        lines.append(f"[PRICE] {item['price']} [/PRICE]")
        if item['image']:
            lines.append(f"Image: {item['image']}")
        if item['description']:
            lines.append(f"Description: {item['description']}")
        lines.append('---')
    return '\n'.join(lines)


def _serialize_cta(cta_buttons: list[dict]) -> str:
    """Serialize CTA buttons to Semantic Markdown."""
    lines = []
    for btn in cta_buttons[:20]:  # Cap at 20 CTAs
        lines.append(
            f"[ACTION_BUTTON] \"{btn['label']}\" → {btn['href']} "
            f"(category: {btn['category']}, score: {btn['weight']})"
        )
    return '\n'.join(lines)


def _serialize_tables(tables: list[dict]) -> str:
    """
    Serialize HTML tables to Self-Describing Rows.
    Instead of raw tables, this repeats headers for EVERY row to ensure
    the LLM never loses context during chunked retrieval.
    """
    lines = []
    for table in tables:
        caption = table['caption'] or "Unnamed Data Table"
        lines.append(f"## DATA TABLE: {caption}")

        # Column headers (labels)
        labels = table['headers']
        col_count = len(labels) if labels else (
            len(table['rows'][0]) if table['rows'] else 0
        )
        if col_count == 0:
            continue

        if not labels:
            labels = [f"Column_{i+1}" for i in range(col_count)]

        # Emit rows as self-describing key-value pairs
        for row in table['rows'][:80]:  # Cap at 80 rows
            row_parts = []
            for i in range(min(len(row), col_count)):
                val = row[i].strip()
                if val:
                    # e.g., [Team: St. Louis Blues]
                    row_parts.append(f"{labels[i]}: {val}")
            
            if row_parts:
                lines.append(f"[ROW] {' | '.join(row_parts)}")

        lines.append('')

    return '\n'.join(lines)


def _serialize_metadata(metadata: dict) -> str:
    """Serialize page metadata to Semantic Markdown."""
    lines = []
    if metadata.get('page_title'):
        lines.append(f"[PAGE_TITLE] {metadata['page_title']}")
    if metadata.get('meta_description'):
        lines.append(f"[META_DESCRIPTION] {metadata['meta_description']}")
    if metadata.get('hero_text'):
        lines.append(f"[HERO_TEXT] {metadata['hero_text']}")
    if metadata.get('breadcrumb'):
        lines.append(f"[BREADCRUMB] {metadata['breadcrumb']}")
    if lines:
        lines.append('')
    return '\n'.join(lines)


def _serialize_footer(metadata: dict) -> str:
    """Serialize footer links."""
    if not metadata.get('footer_links'):
        return ''
    lines = ['[FOOTER]']
    for link in metadata['footer_links'][:15]:
        lines.append(f"- {link['text']} ({link['href']})")
    lines.append('[/FOOTER]')
    return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════════
# RAW TEXT FALLBACK
# ══════════════════════════════════════════════════════════════════════

def _extract_raw_text(soup: BeautifulSoup) -> str:
    """
    Fallback: Extract all visible text content from the page for sections
    not captured by the heuristic detectors. This ensures we never miss
    content on simple landing pages, college sites, etc.
    """
    body = soup.find('body')
    if not body:
        return ''

    # Get major content sections
    sections = []
    for tag in body.find_all(['header', 'main', 'section', 'article', 'div', 'aside']):
        # Only top-level or shallow containers
        depth = 0
        parent = tag.parent
        while parent and parent != body:
            depth += 1
            parent = parent.parent
        if depth > 3:
            continue

        text = tag.get_text(separator='\n', strip=True)
        if text and len(text) > 50:
            # Get a heading for context
            heading = tag.find(['h1', 'h2', 'h3', 'h4'])
            heading_text = heading.get_text(strip=True) if heading else ''

            section_text = ''
            if heading_text:
                section_text += f"## {heading_text}\n"

            # Get paragraphs
            for p in tag.find_all(['p', 'li']):
                p_text = p.get_text(strip=True)
                if p_text and len(p_text) > 10:
                    section_text += f"{p_text}\n"

            if section_text.strip():
                sections.append(section_text.strip())

    # Deduplicate overlapping sections
    unique = []
    for s in sections:
        # Skip if >80% of this section's text is already in a previous one
        is_dup = False
        for u in unique:
            if len(s) > 30 and s[:30] in u:
                is_dup = True
                break
        if not is_dup:
            unique.append(s)

    return '\n\n'.join(unique[:20])  # Cap at 20 sections


# ══════════════════════════════════════════════════════════════════════
# MASTER ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════

def build_semantic_markdown(html: str, base_url: str) -> str:
    """
    Master pipeline: parse HTML → run all heuristic stages → serialize
    to a single Semantic Markdown document.

    Execution order (per spec):
      1. Parse + strip noise
      2. Extract metadata (title, meta, hero, breadcrumb)
      3. Detect navigation
      4. Detect grids (before prices — so prices group correctly)
      5. Extract standalone prices
      6. Map CTAs
      7. Extract tables
      8. Raw text fallback
      9. Assemble document
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Strip noise tags
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()

    # Run all detection stages
    metadata = extract_page_metadata(soup)
    nav_blocks = detect_navigation(soup, base_url)
    grids = detect_grid(soup)
    price_items = extract_prices(soup)
    cta_buttons = map_cta(soup)
    tables = extract_tables(soup)

    # Collect grid item titles for dedup with standalone prices
    grid_titles = set()
    for grid in grids:
        for item in grid['items']:
            if item.get('title'):
                grid_titles.add(item['title'])

    # Assemble the Semantic Markdown document
    doc_parts = []

    # 1. Page metadata
    md_meta = _serialize_metadata(metadata)
    if md_meta:
        doc_parts.append(md_meta)

    # 2. Navigation
    md_nav = _serialize_navigation(nav_blocks)
    if md_nav:
        doc_parts.append(md_nav)

    # 3. Grids (with nested items)
    md_grids = _serialize_grids(grids)
    if md_grids:
        doc_parts.append(md_grids)

    # 4. Standalone price items
    md_prices = _serialize_prices(price_items, grid_titles)
    if md_prices:
        doc_parts.append(md_prices)

    # 5. Tables
    md_tables = _serialize_tables(tables)
    if md_tables:
        doc_parts.append(md_tables)

    # 6. CTAs
    md_cta = _serialize_cta(cta_buttons)
    if md_cta:
        doc_parts.append(md_cta)

    # 7. Footer
    md_footer = _serialize_footer(metadata)
    if md_footer:
        doc_parts.append(md_footer)

    # 8. Raw text fallback
    raw_text = _extract_raw_text(soup)
    if raw_text:
        doc_parts.append('## RAW PAGE CONTENT\n' + raw_text)

    # Join and apply length cap
    full_doc = '\n\n'.join(doc_parts)

    # Clean up encoding artifacts
    full_doc = full_doc.replace('Â£', '£').replace('Â', '')

    if len(full_doc) > MAX_OUTPUT_LENGTH:
        full_doc = full_doc[:MAX_OUTPUT_LENGTH]
        full_doc += '\n\n[TRUNCATED: Document exceeded maximum length]'

    return full_doc
