

\# Universal Semantic Scraper (Web-GPT) — Detailed Technical Specification

\#\# Complete Implementation Document for Autonomous Coding Agent

\---

Below is the full, expanded technical specification document. As requested, \*\*no source code is generated\*\* — only the detailed architectural descriptions, pseudocode logic, step-by-step instructions, configuration schemas, and testing protocols that an autonomous coding agent (e.g., Antigravity) would follow to implement every module.

\---

\# DOCUMENT OVERVIEW

| Metadata | Detail |  
|---|---|  
| \*\*Project Name\*\* | Universal Semantic Scraper (Web-GPT) |  
| \*\*Version\*\* | 2.0 — Universal Heuristic Architecture |  
| \*\*Status\*\* | Pending Approval → Implementation |  
| \*\*Primary Files Affected\*\* | \`ai\_engine/scraper.py\`, \`core/views.py\`, \`celery\_app/tasks.py\`, \`tests/\` |  
| \*\*Objective\*\* | Replace all site-specific CSS selectors with a heuristic pattern-matching engine that can identify navigation, prices, product grids, and calls-to-action on \*\*any\*\* website without manual configuration. |  
| \*\*Target Agent\*\* | Autonomous coding agent (Antigravity or equivalent) |

\---

\# TABLE OF CONTENTS

1\. \*\*Module 1 — Heuristic Detection Engine (\`scraper.py\`)\*\*  
   \- 1.1 Navigation Logic  
   \- 1.2 Price Extraction  
   \- 1.3 Visual Grid Recognition  
   \- 1.4 CTA Mapping  
   \- 1.5 Master Orchestration Pipeline

2\. \*\*Module 2 — Backend Integration (\`views.py\` & Core)\*\*  
   \- 2.1 Semantic Markdown Schema  
   \- 2.2 Structure-Agnostic Prompting  
   \- 2.3 RAG Pipeline Update

3\. \*\*Module 3 — Infrastructure & Performance\*\*  
   \- 3.1 Celery Worker Configuration  
   \- 3.2 Caching Strategy  
   \- 3.3 Timeout & Retry Policies

4\. \*\*Module 4 — Testing & Validation Framework\*\*  
   \- 4.1 Regression Protocol (books.toscrape.com)  
   \- 4.2 Cross-Domain Benchmarks  
   \- 4.3 Logic Verification Queries  
   \- 4.4 Scoring Rubric

5\. \*\*Step-by-Step Implementation Guide for the Agent\*\*

\---

\# MODULE 1 — HEURISTIC DETECTION ENGINE (\`scraper.py\`)

\> \*\*Guiding Principle:\*\* The scraper must never rely on a known class name, ID, or site-specific DOM path. Every detection rule must be expressed as a \*structural heuristic\* — a pattern that describes \*\*what a component looks like\*\* rather than \*\*where it lives on a particular site\*\*.

\---

\#\# 1.1 Navigation Logic — \`\[NAVIGATION\_MENU\]\`

\#\#\# 1.1.1 Purpose

Identify the primary navigation menu(s) on any page so the LLM can answer questions like \*"What are the main sections of this website?"\* or \*"Show me the categories."\*

\#\#\# 1.1.2 Detection Criteria (Ordered by Priority)

| Priority | Rule ID | Description | Threshold |  
|---|---|---|---|  
| P0 | NAV-TAG | Any \`\<nav\>\` element is an immediate candidate. | Element exists |  
| P1 | LIST-DENSITY | Any \`\<ul\>\` or \`\<ol\>\` where \*\*more than 60 %\*\* of direct \`\<li\>\` children contain at least one \`\<a\>\` (anchor) tag. | \`link\_ratio ≥ 0.60\` |  
| P2 | LINK-COUNT | The candidate container holds \*\*≥ 5 internal links\*\* (same-origin \`href\`). | \`internal\_link\_count ≥ 5\` |  
| P3 | POSITION-HINT | The candidate appears in the \*\*top 25 %\*\* of the page's vertical layout (approximated by DOM order or, if available, computed CSS \`offsetTop\`). | \`vertical\_position ≤ 0.25 × page\_height\` |  
| P4 | ARIA/ROLE | Element or ancestor carries \`role="navigation"\` or \`aria-label\` containing keywords: \*nav, menu, navigation, categories\*. | Attribute match |

\#\#\# 1.1.3 Scoring Model

Each candidate element receives a \*\*Navigation Confidence Score (NCS)\*\*:

\`\`\`  
NCS \= (NAV-TAG × 30\) \+ (LIST-DENSITY × 25\) \+ (LINK-COUNT × 20\) \+ (POSITION-HINT × 15\) \+ (ARIA/ROLE × 10\)  
\`\`\`

\- Each factor is binary (0 or 1\) multiplied by its weight.  
\- \*\*Acceptance threshold:\*\* NCS ≥ 50\.  
\- All elements scoring ≥ 50 are tagged \`\[NAVIGATION\_MENU\]\`.  
\- If \*\*no\*\* element scores ≥ 50, lower threshold to 35 and accept the single highest-scoring element (graceful degradation).

\#\#\# 1.1.4 Output Format

For each accepted navigation element, the engine must emit a semantic block:

\`\`\`  
\[NAVIGATION\_MENU\]  
\- Home  
\- Products  
\- About Us  
\- Contact  
\- Blog  
\[/NAVIGATION\_MENU\]  
\`\`\`

Each bullet is the \*\*visible text\*\* of the anchor, followed by its \`href\` in parentheses if it is an internal link.

\#\#\# 1.1.5 Edge Cases & Handling

| Edge Case | Handling |  
|---|---|  
| Mega-menus (nested \`\<ul\>\` with sub-categories) | Flatten to two levels maximum; indent sub-items with two spaces. |  
| Footer navigation | Will likely fail POSITION-HINT but may pass other checks. Tag as \`\[FOOTER\_MENU\]\` if position is in the bottom 20 % of the DOM. |  
| Hamburger / mobile-only menus | If the \`\<nav\>\` or \`\<ul\>\` is inside an element with \`display:none\` or a class containing \*mobile, hamburger, collapsed\*, still extract it but add a metadata flag: \`hidden: true\`. |  
| Single-page apps (SPA) | If initial HTML yields no candidates, the agent must note that a headless rendering step (Playwright/Puppeteer) is required before heuristic analysis. |

\---

\#\# 1.2 Price Extraction — \`\[PRICE\]\` and \`\#\#\# ITEM POINT\`

\#\#\# 1.2.1 Purpose

Detect any monetary value on the page and group it with its surrounding context (product name, image, description) to form an \`\#\#\# ITEM POINT\` block.

\#\#\# 1.2.2 Currency Regex Specification

\*\*Primary Pattern:\*\*

\`\`\`  
PRICE\_REGEX \= /(\[£$€¥₹₩₪R$\]\\s?\\d{1,3}(?:\[,.\\s\]?\\d{3})\*(?:\[.,\]\\d{1,2})?)/g  
\`\`\`

\*\*Supplementary Patterns (to catch text-prefix currencies):\*\*

\`\`\`  
PRICE\_TEXT\_REGEX \= /(USD|EUR|GBP|INR|AUD|CAD|JPY|CNY)\\s?\\d{1,3}(?:\[,.\\s\]?\\d{3})\*(?:\[.,\]\\d{1,2})?/gi  
\`\`\`

\*\*Post-decimal normalization rules:\*\*

| Raw Match | Normalized Value |  
|---|---|  
| \`$1,299.99\` | \`1299.99\` |  
| \`€ 1.299,99\` (European) | \`1299.99\` |  
| \`£20\` | \`20.00\` |  
| \`₹ 4,500\` | \`4500.00\` |

The engine must detect the \*\*locale convention\*\* by checking whether the last separator has two digits after it (decimal) or three (thousands).

\#\#\# 1.2.3 Parent-Element Grouping Algorithm

Once a price match is found in a text node:

1\. \*\*Walk Up\*\* the DOM tree from the text node, stopping at the first ancestor that is a \*\*block-level element\*\* (\`\<div\>\`, \`\<article\>\`, \`\<section\>\`, \`\<li\>\`, \`\<td\>\`) — call this the \*\*Item Container\*\*.  
2\. \*\*Sibling Scan:\*\* Check if the Item Container has siblings with the same tag name and similar class names (see Section 1.3). If yes, each sibling is also an Item Container.  
3\. \*\*Content Extraction\*\* from each Item Container:  
   \- \*\*Title:\*\* The first \`\<h1\>\`–\`\<h6\>\`, or the first \`\<a\>\` text, or the first text node with \`font-size\` larger than the body default.  
   \- \*\*Price:\*\* The matched regex value.  
   \- \*\*Image:\*\* The first \`\<img\>\` \`src\` or \`srcset\` within the container.  
   \- \*\*Description:\*\* Any \`\<p\>\` text, truncated to 200 characters.  
   \- \*\*Link:\*\* The first \`\<a\>\` \`href\` in the container.

\#\#\# 1.2.4 Output Format

\`\`\`  
\#\#\# ITEM POINT  
Title: "A Light in the Attic"  
\[PRICE\] £51.77 \[/PRICE\]  
Image: /media/cache/fe/72/fe72f0532301ec28892ae79a629a293c.jpg  
Description: "It's hard to imagine a world without A Light in the Attic..."  
Link: /catalogue/a-light-in-the-attic\_1000/index.html  
\[ACTION\_BUTTON\] "Add to basket" → /basket/add/1000/  
\---  
\`\`\`

\#\#\# 1.2.5 Disambiguation Rules

| Scenario | Rule |  
|---|---|  
| Multiple prices in one container (e.g., original \+ sale price) | Tag the higher value as \`\[PRICE\_ORIGINAL\]\` and the lower as \`\[PRICE\_SALE\]\`. |  
| Shipping cost ("+ $5.99 shipping") | If the text node contains keywords \*shipping, delivery, freight\*, tag as \`\[PRICE\_SHIPPING\]\` and \*\*do not\*\* create a separate ITEM POINT. |  
| Price range ("$10 – $25") | Tag as \`\[PRICE\_RANGE\_LOW\]\` and \`\[PRICE\_RANGE\_HIGH\]\`. |  
| Non-product prices (e.g., "$0 setup fee" on a SaaS page) | Still tag as \`\[PRICE\]\`; the LLM prompt will handle contextual interpretation. |

\---

\#\# 1.3 Visual Grid Recognition — Repeated Structure Detection

\#\#\# 1.3.1 Purpose

Detect product cards, blog post cards, team member cards, or any repeating visual unit — without knowing the site's CSS class names.

\#\#\# 1.3.2 Detection Algorithm — "Sibling Similarity Index" (SSI)

\*\*Step 1 — Candidate Parent Identification:\*\*

\- Traverse every element in the DOM.  
\- For each element, count its \*\*direct children\*\*.  
\- If an element has \*\*≥ 3 direct children\*\* with the \*\*same tag name\*\*, it becomes a \*\*Grid Candidate Parent\*\*.

\*\*Step 2 — Class-Name Similarity Calculation:\*\*

For each Grid Candidate Parent, compute the SSI across its qualifying children:

\`\`\`  
SSI \= |intersection(class\_set\_child\_1, class\_set\_child\_2, ..., class\_set\_child\_n)| /  
      |union(class\_set\_child\_1, class\_set\_child\_2, ..., class\_set\_child\_n)|  
\`\`\`

This is essentially a \*\*Jaccard Similarity\*\* applied to the CSS class names of sibling elements.

\*\*Step 3 — Threshold:\*\*

| SSI Value | Interpretation |  
|---|---|  
| ≥ 0.70 | \*\*High confidence\*\* — tag as \`\[CONTENT\_GRID\]\`. |  
| 0.40 – 0.69 | \*\*Medium confidence\*\* — tag as \`\[POSSIBLE\_GRID\]\`; include but flag for LLM review. |  
| \< 0.40 | \*\*Reject\*\* — siblings are structurally dissimilar; not a grid. |

\*\*Step 4 — Sub-Element Consistency Check:\*\*

Within each child of the accepted grid, verify that the \*\*internal structure\*\* is consistent:

\- Do ≥ 80 % of children contain at least one \`\<img\>\`? → Image Grid  
\- Do ≥ 80 % of children contain a price regex match? → Product Grid  
\- Do ≥ 80 % of children contain a \`\<time\>\` or date-pattern text? → Article/Blog Grid

Tag accordingly: \`\[PRODUCT\_GRID\]\`, \`\[ARTICLE\_GRID\]\`, \`\[IMAGE\_GALLERY\]\`, or generic \`\[CONTENT\_GRID\]\`.

\#\#\# 1.3.3 Output Format

\`\`\`  
\[PRODUCT\_GRID\] (12 items detected)  
\#\#\# ITEM POINT  
Title: "Nike Air Max 90"  
\[PRICE\] $130.00 \[/PRICE\]  
Image: /images/air-max-90.jpg  
...  
\#\#\# ITEM POINT  
Title: "Nike Dunk Low"  
\[PRICE\] $110.00 \[/PRICE\]  
Image: /images/dunk-low.jpg  
...  
\[/PRODUCT\_GRID\]  
\`\`\`

\#\#\# 1.3.4 Nested Grid Handling

If a grid child itself contains a sub-grid (e.g., color swatches within a product card), the engine must:

1\. Detect the sub-grid using the same SSI algorithm.  
2\. Tag it as \`\[SUB\_GRID\]\` nested inside the parent \`\#\#\# ITEM POINT\`.  
3\. Limit nesting to \*\*two levels\*\* to prevent runaway recursion.

\---

\#\# 1.4 CTA Mapping — \`\[ACTION\_BUTTON\]\`

\#\#\# 1.4.1 Purpose

Identify interactive elements the user can act on — purchase buttons, signup forms, contact links — so the LLM can answer questions like \*"How do I buy this?"\* or \*"Where do I sign up?"\*

\#\#\# 1.4.2 Keyword Dictionary

The engine maintains a \*\*weighted keyword list\*\* organized by intent category:

| Category | Keywords (case-insensitive) | Weight |  
|---|---|---|  
| \*\*Purchase\*\* | buy, add to cart, add to bag, add to basket, purchase, order now, checkout, shop now | 10 |  
| \*\*Signup / Auth\*\* | sign up, register, create account, join, get started, start free trial, subscribe | 9 |  
| \*\*Contact\*\* | contact us, get in touch, request a quote, book a call, schedule, enquire | 8 |  
| \*\*Information\*\* | learn more, read more, view details, see more, explore, discover | 6 |  
| \*\*Download\*\* | download, get the app, install, free download | 7 |  
| \*\*Social/Share\*\* | share, tweet, pin it, follow us | 3 |

\#\#\# 1.4.3 Element Qualification Criteria

An element is a CTA candidate if it matches \*\*ALL\*\* of the following:

1\. \*\*Tag:\*\* \`\<button\>\`, \`\<a\>\`, \`\<input type="submit"\>\`, or any element with \`role="button"\`.  
2\. \*\*Visibility:\*\* Not hidden via \`display:none\`, \`visibility:hidden\`, \`opacity:0\`, or \`aria-hidden="true"\`.  
3\. \*\*Text Match:\*\* The element's \`innerText\` (or \`value\` for inputs) contains at least one keyword from the dictionary above.  
4\. \*\*Size Heuristic (optional, if CSS is available):\*\* The element's computed width is ≥ 60 px and height is ≥ 30 px (to filter out tiny icon buttons).

\#\#\# 1.4.4 Scoring & Labeling

\`\`\`  
CTA\_SCORE \= keyword\_weight \+ (is\_button\_tag × 3\) \+ (has\_distinct\_background\_color × 2\) \+ (is\_above\_fold × 2\)  
\`\`\`

Tag format:

\`\`\`  
\[ACTION\_BUTTON\] "Add to Cart" → /basket/add/1234/ (category: Purchase, score: 15\)  
\`\`\`

\#\#\# 1.4.5 Deduplication

If the same CTA text and \`href\` appear multiple times (e.g., "Add to Cart" in a grid), emit it \*\*once\*\* at the grid level with a count:

\`\`\`  
\[ACTION\_BUTTON\] "Add to Cart" (×12 instances across grid items)  
\`\`\`

Within individual \`\#\#\# ITEM POINT\` blocks, still include the specific \`href\` for each item.

\---

\#\# 1.5 Master Orchestration Pipeline

The four heuristic modules above must execute in a defined sequence on any given HTML document:

\#\#\# Pipeline Order

\`\`\`  
Step 1: FETCH        → Retrieve raw HTML (requests or headless browser)  
Step 2: PARSE        → Build DOM tree (BeautifulSoup / lxml)  
Step 3: NAV-DETECT   → Run Navigation Logic (§1.1) → emit \[NAVIGATION\_MENU\] blocks  
Step 4: GRID-DETECT  → Run Visual Grid Recognition (§1.3) → identify containers  
Step 5: PRICE-DETECT → Run Price Extraction (§1.2) within grid containers first, then page-wide → emit \#\#\# ITEM POINT blocks  
Step 6: CTA-DETECT   → Run CTA Mapping (§1.4) → inject \[ACTION\_BUTTON\] into ITEM POINTs and page-level  
Step 7: ASSEMBLE     → Combine all semantic blocks into a single Semantic Markdown document  
Step 8: RETURN       → Pass the Semantic Markdown to the RAG indexer  
\`\`\`

\#\#\# Why This Order Matters

\- \*\*Grid detection before price detection\*\* ensures that prices are grouped correctly within their parent item containers rather than floating as orphan values.  
\- \*\*CTA detection last\*\* allows CTAs to be injected into already-formed ITEM POINT blocks.

\#\#\# Conflict Resolution

| Conflict | Resolution |  
|---|---|  
| An element is tagged as both \`\[NAVIGATION\_MENU\]\` and \`\[CONTENT\_GRID\]\` | Navigation takes priority; remove from grid candidates. |  
| A price appears outside any detected grid | Emit as a standalone \`\#\#\# ITEM POINT\` with a flag: \`(isolated: true)\`. |  
| A CTA keyword appears inside a navigation link (e.g., "Shop" in the main nav) | Tag as both \`\[NAVIGATION\_MENU\]\` item and \`\[ACTION\_BUTTON\]\`; the LLM prompt will handle context. |

\---

\# MODULE 2 — BACKEND INTEGRATION (\`views.py\` & Core)

\---

\#\# 2.1 Semantic Markdown Schema

\#\#\# 2.1.1 Purpose

Define a \*\*standardized intermediate representation\*\* between raw HTML and the LLM's context window. This "Semantic Markdown" acts as the universal language the RAG pipeline speaks, regardless of the source website.

\#\#\# 2.1.2 Tag Inventory

| Tag | Opens / Closes | Description |  
|---|---|---|  
| \`\[NAVIGATION\_MENU\]\` / \`\[/NAVIGATION\_MENU\]\` | Block | Wraps an identified navigation structure. |  
| \`\[FOOTER\_MENU\]\` / \`\[/FOOTER\_MENU\]\` | Block | Navigation identified in the bottom 20 % of the page. |  
| \`\[PRODUCT\_GRID\]\` / \`\[/PRODUCT\_GRID\]\` | Block | Wraps a detected product grid. Contains count metadata. |  
| \`\[ARTICLE\_GRID\]\` / \`\[/ARTICLE\_GRID\]\` | Block | Wraps a detected blog/article grid. |  
| \`\[CONTENT\_GRID\]\` / \`\[/CONTENT\_GRID\]\` | Block | Generic grid (not clearly product or article). |  
| \`\#\#\# ITEM POINT\` | Block start (ends at next \`---\` or next \`\#\#\# ITEM POINT\`) | Single item/card within a grid or standalone. |  
| \`\[PRICE\]\` / \`\[/PRICE\]\` | Inline | Wraps a detected monetary value. |  
| \`\[PRICE\_ORIGINAL\]\` / \`\[/PRICE\_ORIGINAL\]\` | Inline | Original (struck-through) price. |  
| \`\[PRICE\_SALE\]\` / \`\[/PRICE\_SALE\]\` | Inline | Discounted/sale price. |  
| \`\[PRICE\_RANGE\_LOW\]\` / \`\[/PRICE\_RANGE\_LOW\]\` | Inline | Lower bound of a price range. |  
| \`\[PRICE\_RANGE\_HIGH\]\` / \`\[/PRICE\_RANGE\_HIGH\]\` | Inline | Upper bound of a price range. |  
| \`\[PRICE\_SHIPPING\]\` / \`\[/PRICE\_SHIPPING\]\` | Inline | Shipping/delivery cost. |  
| \`\[ACTION\_BUTTON\]\` | Inline | A detected CTA with text, URL, category, and score. |  
| \`\[PAGE\_TITLE\]\` | Inline | The \`\<title\>\` tag or first \`\<h1\>\` content. |  
| \`\[META\_DESCRIPTION\]\` | Inline | The \`\<meta name="description"\>\` content. |  
| \`\[HERO\_TEXT\]\` | Block | Large heading text detected in the top viewport area. |  
| \`\[FORM\]\` / \`\[/FORM\]\` | Block | A detected \`\<form\>\` with field labels listed. |

\#\#\# 2.1.3 Full Document Template

\`\`\`  
\[PAGE\_TITLE\] "Nike. Just Do It. Nike.com"  
\[META\_DESCRIPTION\] "Inspiring the world's athletes. Shop shoes, clothing, and accessories."

\[NAVIGATION\_MENU\]  
\- New & Featured → /w/new  
\- Men → /w/mens  
\- Women → /w/womens  
\- Kids → /w/kids  
\- Sale → /w/sale  
\[/NAVIGATION\_MENU\]

\[HERO\_TEXT\] "Summer Essentials — Up to 40% Off"  
\[ACTION\_BUTTON\] "Shop Now" → /w/sale (category: Purchase, score: 15\)

\[PRODUCT\_GRID\] (24 items detected)

\#\#\# ITEM POINT  
Title: "Nike Air Max 90"  
\[PRICE\] $130.00 \[/PRICE\]  
Image: https://static.nike.com/a/images/...  
Description: "The Nike Air Max 90 stays true to its OG..."  
Link: /t/air-max-90-shoe-abc123  
\[ACTION\_BUTTON\] "Add to Bag" → /cart/add/abc123 (category: Purchase, score: 15\)  
\---

\#\#\# ITEM POINT  
Title: "Nike Dunk Low Retro"  
\[PRICE\_ORIGINAL\] $110.00 \[/PRICE\_ORIGINAL\]  
\[PRICE\_SALE\] $87.97 \[/PRICE\_SALE\]  
Image: https://static.nike.com/a/images/...  
Link: /t/dunk-low-retro-shoe-def456  
\[ACTION\_BUTTON\] "Add to Bag" → /cart/add/def456 (category: Purchase, score: 15\)  
\---

\[/PRODUCT\_GRID\]

\[FOOTER\_MENU\]  
\- Gift Cards → /gift-cards  
\- Find a Store → /retail  
\- Become a Member → /membership  
\- Contact Us → /help  
\[/FOOTER\_MENU\]  
\`\`\`

\#\#\# 2.1.4 Mapping Rules (HTML → Semantic Markdown)

The autonomous agent must implement a \*\*mapper function\*\* that takes the tagged DOM (output of Module 1\) and serializes it into the Semantic Markdown string. The rules are:

1\. \*\*Whitespace:\*\* Normalize all whitespace to single spaces within inline text; use single blank lines between blocks.  
2\. \*\*Encoding:\*\* UTF-8 throughout; HTML entities must be decoded (\`\&amp;\` → \`&\`).  
3\. \*\*Image URLs:\*\* Convert relative URLs to absolute using the page's base URL.  
4\. \*\*Truncation:\*\* Any single text field (description, hero text) is capped at \*\*300 characters\*\* with an ellipsis.  
5\. \*\*Total Document Cap:\*\* The entire Semantic Markdown document must not exceed \*\*12,000 tokens\*\* (measured via \`tiktoken\` with the model's tokenizer). If it does, truncate from the bottom of the \`\[PRODUCT\_GRID\]\` (remove the last items first) and append \`\[TRUNCATED: 48 of 120 items shown\]\`.

\---

\#\# 2.2 Structure-Agnostic Prompting

\#\#\# 2.2.1 Design Philosophy

The LLM must never receive instructions that assume a website type. Phrases like \*"This is a bookstore"\* or \*"Look for product listings"\* are \*\*prohibited\*\* in the system prompt. Instead, the prompt teaches the LLM to \*\*read the semantic tags\*\* and infer context.

\#\#\# 2.2.2 System Prompt Template

\`\`\`  
SYSTEM PROMPT (to be set in \_build\_prompt):

"""  
You are a helpful assistant that answers questions about a web page.  
You are given a "Semantic Map" of the page below. This map was generated  
automatically and uses special tags to identify page components:

  • \[NAVIGATION\_MENU\] — The site's navigation links / categories.  
  • \[PRODUCT\_GRID\] / \[ARTICLE\_GRID\] / \[CONTENT\_GRID\] — A repeating set of items.  
  • \#\#\# ITEM POINT — A single item (could be a product, article, service, etc.).  
  • \[PRICE\] — A detected monetary value associated with an item.  
  • \[PRICE\_SALE\] — A discounted/sale price.  
  • \[ACTION\_BUTTON\] — A clickable action the user can take (e.g., buy, sign up).  
  • \[HERO\_TEXT\] — A prominent heading, usually a marketing message.  
  • \[FORM\] — A detected form (signup, contact, search, etc.).

RULES:  
1\. Base ALL answers strictly on the Semantic Map provided. Do not invent information.  
2\. When the user asks about prices, refer to \[PRICE\] tags. If both \[PRICE\_ORIGINAL\]  
   and \[PRICE\_SALE\] exist, note the discount.  
3\. When the user asks about navigation or categories, refer to \[NAVIGATION\_MENU\].  
4\. When the user asks "how to buy" or "how to sign up," refer to \[ACTION\_BUTTON\] tags.  
5\. If the Semantic Map contains \[TRUNCATED\], inform the user that not all items  
   are shown and offer to provide what is available.  
6\. Never assume the type of website. Let the tags tell you what the page contains.  
7\. For comparative questions ("most expensive," "cheapest"), parse all \[PRICE\] values,  
   convert to numeric, and compare.  
"""  
\`\`\`

\#\#\# 2.2.3 User Prompt Template

\`\`\`  
USER PROMPT:

"""  
\=== SEMANTIC MAP START \===  
{semantic\_markdown\_document}  
\=== SEMANTIC MAP END \===

User Question: {user\_question}  
"""  
\`\`\`

\#\#\# 2.2.4 Prompt Update Procedure for the Agent

The autonomous agent must:

1\. Locate the \`\_build\_prompt\` function in \`core/views.py\`.  
2\. Remove any existing system prompt text that references specific websites, CSS selectors, or site types.  
3\. Replace with the system prompt template above, inserting \`{semantic\_markdown\_document}\` and \`{user\_question}\` dynamically.  
4\. Ensure that the Semantic Markdown document is inserted \*\*before\*\* the user question so the LLM reads context first.

\---

\#\# 2.3 RAG Pipeline Update

\#\#\# 2.3.1 Chunking Strategy

Since the Semantic Markdown has clear block delimiters, the RAG chunking must be \*\*tag-aware\*\*:

| Chunk Boundary | Max Chunk Size | Overlap |  
|---|---|---|  
| Each \`\#\#\# ITEM POINT ... \---\` block \= 1 chunk | 500 tokens | 0 (items are self-contained) |  
| \`\[NAVIGATION\_MENU\] ... \[/NAVIGATION\_MENU\]\` \= 1 chunk | 300 tokens | 0 |  
| \`\[HERO\_TEXT\]\` \+ surrounding \`\[ACTION\_BUTTON\]\` \= 1 chunk | 200 tokens | 0 |  
| Any text outside tagged blocks \= 1 chunk per paragraph | 500 tokens | 50 tokens |

\#\#\# 2.3.2 Embedding Metadata

Each chunk sent to the vector store must carry metadata:

\`\`\`  
{  
  "chunk\_id": "uuid",  
  "source\_url": "https://...",  
  "semantic\_type": "ITEM\_POINT | NAVIGATION | HERO | GENERAL",  
  "has\_price": true/false,  
  "price\_value": 130.00,  // null if no price  
  "timestamp": "2025-01-15T10:30:00Z"  
}  
\`\`\`

This allows \*\*filtered retrieval\*\* — e.g., when a user asks \*"What is the most expensive item?"\*, the retriever can pre-filter to chunks where \`has\_price \== true\` and sort by \`price\_value\` descending before sending to the LLM.

\#\#\# 2.3.3 Retrieval Query Enhancement

Before the user question is sent to the retriever, the backend must:

1\. \*\*Classify the question intent\*\* using a lightweight keyword check:  
   \- Contains "price," "cost," "expensive," "cheap" → add filter \`has\_price: true\`  
   \- Contains "navigate," "menu," "categories," "sections" → add filter \`semantic\_type: NAVIGATION\`  
   \- Contains "buy," "purchase," "sign up," "contact" → add filter \`semantic\_type: ITEM\_POINT or GENERAL\` (looking for ACTION\_BUTTON)  
2\. \*\*Retrieve top-k chunks\*\* (default k=5; increase to k=10 for comparative questions).  
3\. \*\*Assemble context\*\* and pass to the LLM with the structure-agnostic prompt.

\---

\# MODULE 3 — INFRASTRUCTURE & PERFORMANCE

\---

\#\# 3.1 Celery Worker Configuration

\#\#\# 3.1.1 Rationale

Heuristic pattern matching (DOM traversal, SSI calculation, regex scanning) is \*\*CPU-intensive\*\*. Running it synchronously in the Django request-response cycle would:

\- Block the web server thread for 2–15 seconds depending on page complexity.  
\- Degrade frontend latency and user experience.  
\- Risk HTTP timeouts on large pages.

\*\*Solution:\*\* Offload all scraping and heuristic analysis to a \*\*Celery background worker\*\*.

\#\#\# 3.1.2 Task Definition

A new Celery task must be defined (in \`celery\_app/tasks.py\` or \`ai\_engine/tasks.py\`):

\*\*Task Name:\*\* \`analyze\_page\`

\*\*Inputs:\*\*  
| Parameter | Type | Description |  
|---|---|---|  
| \`url\` | string | The URL to scrape and analyze. |  
| \`use\_headless\` | boolean | Whether to use a headless browser (Playwright) instead of plain \`requests\`. Default: \`false\`. |  
| \`max\_depth\` | integer | Number of pagination/sub-pages to follow. Default: \`1\` (current page only). |

\*\*Outputs:\*\*  
| Field | Type | Description |  
|---|---|---|  
| \`semantic\_markdown\` | string | The full Semantic Markdown document. |  
| \`metadata\` | dict | Page title, URL, item count, detected page type, processing time. |  
| \`status\` | string | \`success\`, \`partial\` (truncated), or \`error\`. |

\#\#\# 3.1.3 Worker Configuration

\`\`\`  
\# Celery Configuration (to be placed in settings or celery.py)

CELERY\_BROKER\_URL            \= "redis://localhost:6379/0"  
CELERY\_RESULT\_BACKEND        \= "redis://localhost:6379/1"  
CELERY\_TASK\_SERIALIZER       \= "json"  
CELERY\_RESULT\_SERIALIZER     \= "json"  
CELERY\_ACCEPT\_CONTENT        \= \["json"\]  
CELERY\_TASK\_ACKS\_LATE        \= True          \# Re-queue if worker crashes mid-task  
CELERY\_WORKER\_PREFETCH\_MULT  \= 1             \# One task at a time per worker (CPU-bound)  
CELERY\_TASK\_SOFT\_TIME\_LIMIT  \= 60            \# Soft limit: 60 seconds  
CELERY\_TASK\_TIME\_LIMIT       \= 90            \# Hard kill: 90 seconds  
CELERY\_WORKER\_CONCURRENCY    \= 2             \# 2 concurrent workers (adjust per CPU cores)  
CELERY\_TASK\_ROUTES \= {  
    "ai\_engine.tasks.analyze\_page": {"queue": "scraper\_queue"},  
}  
\`\`\`

\#\#\# 3.1.4 Queue Topology

\`\`\`  
                   ┌─────────────┐  
  Django View ───► │ Redis Broker │  
                   └──────┬──────┘  
                          │  
              ┌───────────┼───────────┐  
              ▼                       ▼  
     ┌────────────────┐     ┌────────────────┐  
     │ Scraper Worker 1│     │ Scraper Worker 2│  
     │ (scraper\_queue) │     │ (scraper\_queue) │  
     └────────┬───────┘     └────────┬───────┘  
              │                       │  
              ▼                       ▼  
     ┌────────────────────────────────────┐  
     │         Redis Result Backend       │  
     └────────────────┬───────────────────┘  
                      │  
                      ▼  
              Django View (polls for result or uses WebSocket callback)  
\`\`\`

\#\#\# 3.1.5 Frontend Integration Flow

1\. \*\*User submits a URL\*\* via the chat interface.  
2\. \*\*Django view\*\* dispatches \`analyze\_page.delay(url=..., use\_headless=False)\`.  
3\. \*\*View returns immediately\*\* with a task ID and a message: \*"Analyzing the page... This may take a few seconds."\*  
4\. \*\*Frontend polls\*\* \`/api/task-status/\<task\_id\>/\` every 2 seconds (or listens on a WebSocket channel).  
5\. \*\*When task completes\*\*, the Semantic Markdown is stored (database or cache) and the chat becomes active for questions.

\---

\#\# 3.2 Caching Strategy

| Cache Layer | Key | TTL | Purpose |  
|---|---|---|---|  
| \*\*Page HTML Cache\*\* | \`html:{url\_hash}\` | 1 hour | Avoid re-fetching the same URL within a short window. |  
| \*\*Semantic Markdown Cache\*\* | \`semantic:{url\_hash}\` | 1 hour | Avoid re-running heuristics if the HTML hasn't changed. |  
| \*\*LLM Response Cache\*\* | \`llm:{url\_hash}:{question\_hash}\` | 30 minutes | Avoid re-querying the LLM for identical questions on the same page. |

Cache invalidation: If the user explicitly requests a "refresh" or submits the same URL again, bypass cache.

\---

\#\# 3.3 Timeout & Retry Policies

| Scenario | Policy |  
|---|---|  
| HTTP fetch fails (network error, 5xx) | Retry up to \*\*3 times\*\* with exponential backoff (2s, 4s, 8s). |  
| HTTP 403/429 (blocked/rate-limited) | Switch to headless browser mode on first retry; if still blocked, return error with message: \*"This site appears to block automated access."\* |  
| Heuristic analysis exceeds soft time limit (60s) | Log a warning; return partial results with \`status: partial\`. |  
| Heuristic analysis exceeds hard time limit (90s) | Task is killed; return \`status: error\` with message: \*"Page too complex for analysis within time limits."\* |  
| Headless browser render timeout | Set Playwright's \`page.goto()\` timeout to \*\*30 seconds\*\*. On timeout, fall back to raw HTML if available. |

\---

\# MODULE 4 — TESTING & VALIDATION FRAMEWORK

\---

\#\# 4.1 Regression Protocol — \`books.toscrape.com\`

\#\#\# 4.1.1 Objective

Ensure that the new universal heuristic engine produces \*\*equal or better results\*\* compared to the old site-specific selectors when analyzing the legacy test site.

\#\#\# 4.1.2 Test Page

\*\*URL:\*\* \`https://books.toscrape.com/\`

\#\#\# 4.1.3 Expected Detections

| Component | Expected Result | Acceptance Criteria |  
|---|---|---|  
| \*\*Navigation Menu\*\* | Left sidebar with 50 book categories (Travel, Mystery, etc.) | ≥ 45 categories detected and listed under \`\[NAVIGATION\_MENU\]\`. |  
| \*\*Product Grid\*\* | 20 book cards on the main page | \`\[PRODUCT\_GRID\]\` detected with item count between 18 and 20\. |  
| \*\*Prices\*\* | 20 prices in GBP (e.g., £51.77) | All 20 \`\[PRICE\]\` tags present; values match the page exactly. |  
| \*\*Titles\*\* | 20 book titles | Each \`\#\#\# ITEM POINT\` contains a non-empty \`Title\` field. |  
| \*\*CTAs\*\* | "Add to basket" buttons (if present on listing page) or "Add to basket" on detail page | At least one \`\[ACTION\_BUTTON\]\` detected per item. |  
| \*\*Pagination\*\* | "Next" link at the bottom | Detected as \`\[ACTION\_BUTTON\]\` with category: Information (or as a navigation element). |

\#\#\# 4.1.4 Automated Test Steps

1\. Run \`analyze\_page(url="https://books.toscrape.com/")\`.  
2\. Parse the returned Semantic Markdown.  
3\. Assert: \`\[NAVIGATION\_MENU\]\` block exists and contains ≥ 45 bullet items.  
4\. Assert: \`\[PRODUCT\_GRID\]\` block exists.  
5\. Assert: Count of \`\#\#\# ITEM POINT\` blocks ≥ 18\.  
6\. Assert: Count of \`\[PRICE\]\` tags ≥ 18\.  
7\. Assert: All \`\[PRICE\]\` values match the regex \`/£\\d+\\.\\d{2}/\`.  
8\. Assert: Each \`\#\#\# ITEM POINT\` has a non-empty \`Title\`.

\#\#\# 4.1.5 Regression Pass Criteria

\*\*All 8 assertions must pass.\*\* If any fail, the agent must not proceed to cross-domain testing.

\---

\#\# 4.2 Cross-Domain Benchmarks

\#\#\# 4.2.1 Test Matrix

| \# | Site | Type | URL | Key Challenges |  
|---|---|---|---|---|  
| 1 | Nike | E-commerce (complex) | \`https://www.nike.com/w/mens-shoes-nik1zy7ok\` | Dynamic rendering (SPA), lazy-loaded images, mega-menu navigation. |  
| 2 | Local Bakery (example) | Small business landing | \`https://www.example-bakery.com/\` (substitute with any real local business) | Minimal structure, no grid, prices may be in paragraph text, single-page layout. |  
| 3 | Medium Blog | Content / blog | \`https://medium.com/tag/technology\` | Article cards, no prices, "Read more" CTAs, author metadata. |  
| 4 | Amazon Product Page | E-commerce (single product) | \`https://www.amazon.com/dp/B0CXXXXXXX\` (any active ASIN) | Multiple price formats, "Add to Cart" inside nested divs, review count, star ratings. |  
| 5 | Craigslist | Classifieds | \`https://sfbay.craigslist.org/search/sss\` | Minimal CSS, list-based layout (not grid), prices in title text. |  
| 6 | Stripe Pricing Page | SaaS / pricing | \`https://stripe.com/pricing\` | Pricing tiers (not products), feature comparison tables, CTAs for each tier. |

\#\#\# 4.2.2 Per-Site Expected Outcomes

\*\*Site 1 — Nike:\*\*  
\- \`\[NAVIGATION\_MENU\]\` with ≥ 5 top-level categories.  
\- \`\[PRODUCT\_GRID\]\` with ≥ 10 items (may be fewer if SPA doesn't fully render).  
\- \`\[PRICE\]\` on each item.  
\- \`\[ACTION\_BUTTON\]\` — at least one instance of text containing "add" or "buy" or "shop."  
\- \*\*Special Note:\*\* If headless rendering is required, the engine must automatically detect the lack of content in raw HTML and flag \`use\_headless: true\`.

\*\*Site 2 — Local Bakery:\*\*  
\- \`\[NAVIGATION\_MENU\]\` — may be minimal (3–5 links); threshold graceful degradation should activate.  
\- \`\[PRODUCT\_GRID\]\` or \`\[CONTENT\_GRID\]\` — may or may not exist; if the page lists items in \`\<p\>\` tags with prices, ITEM POINTs should still be generated.  
\- \`\[PRICE\]\` — at least some prices detected if the menu/pricing is on the page.  
\- \`\[ACTION\_BUTTON\]\` — "Order Now," "Call Us," or "Contact" type buttons.

\*\*Site 3 — Medium:\*\*  
\- \`\[NAVIGATION\_MENU\]\` — top bar with "Home," "Lists," "Membership."  
\- \`\[ARTICLE\_GRID\]\` — detected based on repeated card structures with \`\<time\>\` elements.  
\- \`\[PRICE\]\` — none expected (or possibly a membership price).  
\- \`\[ACTION\_BUTTON\]\` — "Read more," "Get started," "Sign in."

\*\*Site 4 — Amazon Product Page:\*\*  
\- Single \`\#\#\# ITEM POINT\` (not a grid — single product page).  
\- \`\[PRICE\]\` — main price clearly detected.  
\- \`\[PRICE\_ORIGINAL\]\` and \`\[PRICE\_SALE\]\` if a discount is active.  
\- \`\[ACTION\_BUTTON\]\` — "Add to Cart," "Buy Now."  
\- \`\[NAVIGATION\_MENU\]\` — Amazon's department nav.

\*\*Site 5 — Craigslist:\*\*  
\- \`\[CONTENT\_GRID\]\` — list of classified posts.  
\- \`\[PRICE\]\` — inline prices in listing titles (e.g., "$250 — Vintage Table").  
\- Minimal CTAs.

\*\*Site 6 — Stripe:\*\*  
\- \`\[CONTENT\_GRID\]\` — pricing tier cards.  
\- \`\[PRICE\]\` — per-tier pricing (e.g., "2.9% \+ 30¢" — note: percentage-based pricing may not match standard regex; engine should have a secondary pattern for percentage fees).  
\- \`\[ACTION\_BUTTON\]\` — "Start now," "Contact sales."

\#\#\# 4.2.3 Cross-Domain Pass Criteria

For each site, a \*\*Detection Scorecard\*\* is computed:

| Detection Type | Weight | Scoring |  
|---|---|---|  
| Navigation detected | 20% | Full marks if ≥ 1 \`\[NAVIGATION\_MENU\]\` block found. |  
| Grid/list detected | 25% | Full marks if correct grid type identified; half marks if generic \`\[CONTENT\_GRID\]\`. |  
| Prices detected | 25% | \`(detected\_prices / expected\_prices) × 25\`. |  
| CTAs detected | 15% | Full marks if ≥ 1 relevant \`\[ACTION\_BUTTON\]\` found. |  
| Item titles extracted | 15% | \`(items\_with\_titles / total\_items) × 15\`. |

\*\*Minimum passing score per site: 60 / 100.\*\*  
\*\*Minimum average across all 6 sites: 70 / 100.\*\*

\---

\#\# 4.3 Logic Verification Queries

These are standardized natural-language questions to be asked to the LLM after a page has been analyzed. They test whether the \*\*end-to-end pipeline\*\* (scrape → semantic markdown → RAG → LLM response) produces correct answers.

\#\#\# 4.3.1 Universal Questions (Ask on Every Test Site)

| \# | Question | Expected Behavior |  
|---|---|---|  
| Q1 | "What are the navigation options on this page?" | LLM lists items from \`\[NAVIGATION\_MENU\]\`. |  
| Q2 | "How many items are displayed on this page?" | LLM returns a count matching the number of \`\#\#\# ITEM POINT\` blocks (± 2 tolerance). |  
| Q3 | "What is the most expensive item on this page?" | LLM identifies the item with the highest \`\[PRICE\]\` value and states its title and price. |  
| Q4 | "What is the cheapest item on this page?" | LLM identifies the item with the lowest \`\[PRICE\]\` value. |  
| Q5 | "Are there any discounted or sale items?" | LLM checks for \`\[PRICE\_SALE\]\` tags; responds "yes" with details or "no." |  
| Q6 | "How can I purchase / sign up / contact?" | LLM references \`\[ACTION\_BUTTON\]\` tags with category Purchase/Signup/Contact. |  
| Q7 | "Summarize what this page is about." | LLM uses \`\[PAGE\_TITLE\]\`, \`\[META\_DESCRIPTION\]\`, \`\[HERO\_TEXT\]\`, and overall content to give a 2–3 sentence summary. |

\#\#\# 4.3.2 Site-Specific Verification Questions

\*\*books.toscrape.com:\*\*  
| Question | Expected Answer |  
|---|---|  
| "What categories of books are available?" | Lists ≥ 40 categories from the sidebar nav. |  
| "What is the price of 'A Light in the Attic'?" | "£51.77" |  
| "How many books cost more than £50?" | Correct count based on the 20 items on page 1\. |

\*\*Nike:\*\*  
| Question | Expected Answer |  
|---|---|  
| "Show me shoes under $100." | Lists items where \`\[PRICE\]\` \< 100.00, or states none exist on this page. |  
| "What colors are available for the Air Max 90?" | If sub-grid (color swatches) was detected, lists them; otherwise, states "color information not detected." |

\*\*Stripe:\*\*  
| Question | Expected Answer |  
|---|---|  
| "What does the standard pricing plan cost?" | References the relevant \`\[PRICE\]\` in the pricing tier. |  
| "How do I get started?" | References the "Start now" \`\[ACTION\_BUTTON\]\`. |

\#\#\# 4.3.3 Verification Pass Criteria

Each question-answer pair is evaluated on a \*\*3-point scale\*\*:

| Score | Meaning |  
|---|---|  
| \*\*2\*\* | Fully correct — accurate, sourced from semantic map, no hallucination. |  
| \*\*1\*\* | Partially correct — right direction but missing detail or minor inaccuracy. |  
| \*\*0\*\* | Incorrect — wrong answer, hallucination, or "I don't know" when data exists. |

\*\*Per-site minimum:\*\* Average score ≥ 1.3 across all questions.  
\*\*Overall minimum:\*\* Average score ≥ 1.5 across all sites and questions.

\---

\#\# 4.4 Scoring Rubric — Summary

| Test Phase | Weight | Pass Threshold |  
|---|---|---|  
| Regression (books.toscrape.com) | 30% | 8/8 assertions pass |  
| Cross-Domain Detection Scorecard | 40% | ≥ 60/100 per site, ≥ 70/100 average |  
| Logic Verification Queries | 30% | ≥ 1.5 average score across all Q\&A |

\*\*Overall Go / No-Go:\*\* All three phases must independently pass their thresholds.

\---

\# STEP-BY-STEP IMPLEMENTATION GUIDE FOR THE AUTONOMOUS AGENT

\> This section provides the exact sequence of actions the Antigravity agent (or equivalent) must follow. No code is written here — only instructions.

\---

\#\# Phase 0 — Preparation

| Step | Action | Details |  
|---|---|---|  
| 0.1 | \*\*Read the existing codebase\*\* | Understand the current structure of \`ai\_engine/scraper.py\`, \`core/views.py\`, and any existing Celery configuration. |  
| 0.2 | \*\*Identify all site-specific selectors\*\* | Search the codebase for hardcoded class names, IDs, or CSS selectors (e.g., \`side\_categories\`, \`product\_pod\`, \`price\_color\`). List them. |  
| 0.3 | \*\*Create a feature branch\*\* | Branch name: \`feature/universal-heuristic-engine\`. |  
| 0.4 | \*\*Set up test fixtures\*\* | Download and save the HTML of \`books.toscrape.com\` as a local fixture file for offline regression testing. |

\---

\#\# Phase 1 — Heuristic Detection Engine

| Step | Action | Details |  
|---|---|---|  
| 1.1 | \*\*Implement Navigation Detection\*\* | Follow the specification in §1.1. Create a function that accepts a parsed DOM tree and returns a list of \`NavigationBlock\` objects (text \+ hrefs). Use the NCS scoring model. |  
| 1.2 | \*\*Implement Price Extraction\*\* | Follow §1.2. Create regex patterns, the parent-element grouping algorithm, and the normalization logic. Return \`ItemPoint\` objects. |  
| 1.3 | \*\*Implement Grid Recognition\*\* | Follow §1.3. Create the SSI calculator. Identify grid parents and classify them (product, article, generic). |  
| 1.4 | \*\*Implement CTA Mapping\*\* | Follow §1.4. Keyword dictionary, element qualification, scoring. Return \`CTAButton\` objects. |  
| 1.5 | \*\*Implement Master Orchestrator\*\* | Follow §1.5. Wire the four detectors in sequence: NAV → GRID → PRICE → CTA. Handle conflicts per the resolution table. |  
| 1.6 | \*\*Implement Semantic Markdown Serializer\*\* | Follow §2.1. Convert the detected objects into the Semantic Markdown string format. Apply truncation rules. |  
| 1.7 | \*\*Unit test each detector\*\* | Use the saved \`books.toscrape.com\` HTML fixture. Assert per §4.1.4. |

\---

\#\# Phase 2 — Backend Integration

| Step | Action | Details |  
|---|---|---|  
| 2.1 | \*\*Update \`\_build\_prompt\` in \`views.py\`\*\* | Remove all site-specific prompt text. Insert the system prompt template from §2.2.2 and user prompt template from §2.2.3. |  
| 2.2 | \*\*Update RAG chunking logic\*\* | Modify the text splitter to respect semantic tag boundaries (§2.3.1). |  
| 2.3 | \*\*Add metadata to embeddings\*\* | Ensure each chunk carries \`semantic\_type\`, \`has\_price\`, and \`price\_value\` (§2.3.2). |  
| 2.4 | \*\*Implement query intent classification\*\* | Add the lightweight keyword-based filter before retrieval (§2.3.3). |  
| 2.5 | \*\*Integration test\*\* | Scrape \`books.toscrape.com\`, generate Semantic Markdown, index it, and ask Q1–Q7 from §4.3.1. Verify answers. |

\---

\#\# Phase 3 — Infrastructure

| Step | Action | Details |  
|---|---|---|  
| 3.1 | \*\*Define Celery task \`analyze\_page\`\*\* | Follow §3.1.2. Inputs: url, use\_headless, max\_depth. Outputs: semantic\_markdown, metadata, status. |  
| 3.2 | \*\*Configure Celery workers\*\* | Apply settings from §3.1.3. Set up the \`scraper\_queue\`. |  
| 3.3 | \*\*Update Django view for async flow\*\* | Dispatch task, return task ID, implement polling endpoint (§3.1.5). |  
| 3.4 | \*\*Implement caching\*\* | Add Redis-based caching for HTML, Semantic Markdown, and LLM responses (§3.2). |  
| 3.5 | \*\*Implement timeout & retry\*\* | Configure per §3.3. Test with a deliberately slow/blocking URL. |  
| 3.6 | \*\*End-to-end latency test\*\* | Submit a URL via the frontend, measure time from submission to first answerable chat. Target: \< 15 seconds for a typical page. |

\---

\#\# Phase 4 — Testing & Validation

| Step | Action | Details |  
|---|---|---|  
| 4.1 | \*\*Run full regression on books.toscrape.com\*\* | Execute all 8 assertions from §4.1.4. All must pass. |  
| 4.2 | \*\*Run cross-domain benchmarks\*\* | Test on all 6 sites from §4.2.1. Compute Detection Scorecard for each. |  
| 4.3 | \*\*Run logic verification queries\*\* | Ask all universal questions (§4.3.1) and site-specific questions (§4.3.2) on each test site. Score on the 3-point scale. |  
| 4.4 | \*\*Compute overall score\*\* | Apply the rubric from §4.4. If all phases pass, mark the feature as ready for merge. |  
| 4.5 | \*\*Document results\*\* | Create a test report with per-site scores, failure analysis, and any known limitations. |  
| 4.6 | \*\*Submit for human review\*\* | Present the test report and request final approval before merging to main. |

\---

\#\# Phase 5 — Post-Merge

| Step | Action | Details |  
|---|---|---|  
| 5.1 | \*\*Monitor production\*\* | Watch Celery task failure rates, average processing times, and LLM response quality for the first 48 hours. |  
| 5.2 | \*\*Collect user feedback\*\* | If users report poor results on specific sites, add those sites to the cross-domain benchmark suite. |  
| 5.3 | \*\*Iterate on heuristics\*\* | Adjust thresholds (NCS, SSI, keyword weights) based on real-world performance data. |

\---

\# APPENDICES

\#\# Appendix A — Glossary

| Term | Definition |  
|---|---|  
| \*\*Heuristic\*\* | A rule-of-thumb algorithm that makes educated guesses based on structural patterns rather than exact selectors. |  
| \*\*SSI (Sibling Similarity Index)\*\* | A Jaccard similarity metric applied to CSS class names of sibling DOM elements to detect repeated structures. |  
| \*\*NCS (Navigation Confidence Score)\*\* | A weighted score (0–100) indicating how likely a DOM element is to be a navigation menu. |  
| \*\*Semantic Markdown\*\* | A custom markup format using tags like \`\[PRICE\]\`, \`\[NAVIGATION\_MENU\]\`, etc., that serves as the intermediate representation between raw HTML and the LLM context. |  
| \*\*ITEM POINT\*\* | A single detected entity (product, article, service) within the Semantic Markdown. |  
| \*\*Structure-Agnostic\*\* | Designed to work without any prior knowledge of the website's structure or type. |

\#\# Appendix B — Risk Register

| Risk | Likelihood | Impact | Mitigation |  
|---|---|---|---|  
| Heuristics produce false positives (e.g., footer links scored as nav) | Medium | Low | Position-based filtering (§1.1 POSITION-HINT); separate \`\[FOOTER\_MENU\]\` tag. |  
| SPA sites yield empty HTML without headless rendering | High | High | Auto-detect empty body and retry with \`use\_headless: true\` (§3.3). |  
| Regex misses non-standard price formats | Medium | Medium | Supplementary text-prefix regex; periodic regex review based on failed sites. |  
| CPU overload from heuristic processing | Low | Medium | Celery worker concurrency capped at 2; soft/hard time limits (§3.1.3). |  
| LLM hallucinates answers not in Semantic Map | Medium | High | Strong system prompt guardrails (§2.2.2 Rule 1); post-generation answer grounding check. |  
| Anti-bot measures block scraping | High | High | Headless browser fallback; respectful rate limiting; user notification when blocked (§3.3). |

\#\# Appendix C — Dependency List

| Dependency | Purpose | Version (Minimum) |  
|---|---|---|  
| BeautifulSoup4 | HTML parsing & DOM traversal | 4.12 |  
| lxml | Fast HTML/XML parser backend | 4.9 |  
| Celery | Async task queue | 5.3 |  
| Redis | Message broker & cache | 7.0 |  
| Playwright (optional) | Headless browser rendering for SPAs | 1.40 |  
| tiktoken | Token counting for LLM context window management | 0.5 |  
| Django | Web framework | 4.2 |  
| OpenAI / LLM SDK | LLM API integration | Latest stable |

\---

\*\*END OF DOCUMENT\*\*

\*This specification is intended for an autonomous coding agent. No source code has been provided — only architectural decisions, algorithmic specifications, configuration values, and step-by-step instructions. The agent should implement each module according to the detailed criteria above, validate against the testing framework, and submit results for human review before deployment.\*  
