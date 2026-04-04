**WEB-GPT** 

**Universal Semantic Scraper** Technical Specification & Implementation Guide 

**v 1.0 · RAG Architecture Upgrade · Antigravity Agent Runbook** 

| Document Type  | Technical Specification |
| :---- | :---- |
| **Architecture Layer**  | Heuristic Scraper · RAG Backend · Celery Workers |
| **Target Agent**  | Antigravity Autonomous Coding Agent |
| **Status**  | Pending Implementation Approval |
| **Files Modified**  | scraper.py · views.py · celery\_config.py |

■ **Objective** 

Transition Web-GPT from a bookstore-specific CSS-selector pipeline to a fully Universal Heuristic Architecture capable of scraping, mapping, and reasoning about **any** website — e-commerce stores, blogs, SaaS landing pages, or local business sites — without a single line of manual configuration.

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 2 

**Table of Contents** 

**1 Heuristic Detection Engine — scraper.py — Pattern-Matching Core** 1.1 **Navigation / Menu Detection** — \[NAVIGATION\_MENU\] heuristic   
1.2 **Price Extraction Engine** — Regex \+ parent-element grouping 

1.3 **Visual Grid Recognition** — Repeated-structure analysis 

1.4 **CTA Button Mapping** — \[ACTION\_BUTTON\] keyword heuristic 

**2 Semantic Markdown Schema — Standardised HTML** → **Markdown conversion** 2.1 **Tag Reference Table** — Full tag catalogue   
2.2 **Conversion Pipeline** — Step-by-step transformation 

**3 Backend Integration — views.py & Core prompt logic** 

3.1 **Structure-Agnostic Prompting** — \_build\_prompt() redesign 

3.2 **Context Assembly** — Feeding the semantic map to the LLM 

**4 Infrastructure & Performance — Celery worker configuration** 4.1 **Worker Architecture** — Queue design & concurrency   
4.2 **CPU Budget Guidelines** — Heuristic profiling targets 

**5 Testing & Validation Framework — Regression · Cross-domain · Logic** 5.1 **Regression Protocol** — books.toscrape.com legacy suite   
5.2 **Cross-Domain Benchmarks** — Nike, local bakery, SaaS 

5.3 **Logic Verification Queries** — Standard QA question bank 

**6 Step-by-Step Implementation Guide — Sequential agent runbook 7 Open Questions & Risk Register — Performance, edge-cases, roadmap**

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 3 

**0**   
**1Heuristic Detection Engine — scraper.py** 

**Architecture Overview** 

The Heuristic Detection Engine replaces all hard-coded CSS selectors with a four-stage pattern-recognition pipeline. Each stage is independent and contributes semantic tags to a shared **Semantic Map** object that is later serialised to Markdown and fed into the LLM context. 

| Stage  | Module Function  | Output Tag  | Confidence Threshold |
| :---- | :---- | ----- | ----- |
| 1 — Navigation  | detect\_navigation(soup)  | \[NAVIGATION\_MENU\]  | ≥ 5 internal links |
| 2 — Price  | extract\_prices(soup)  | \[PRICE\] / \#\#\# ITEM POINT  | Regex match \+ parent |
| 3 — Grid  | detect\_grid(soup)  | \[PRODUCT\_GRID\]  | ≥ 3 similar siblings |
| 4 — CTA  | map\_cta(soup)  | \[ACTION\_BUTTON\]  | Keyword in text/aria |

 

**1.1 Navigation / Menu Detection** 

A navigation element is defined as any **\<ul\>**, **\<ol\>**, or **\<nav\>** container whose direct or shallow-nested \<a\> tags satisfy both a link-count threshold and an internal-link ratio. This dual gate avoids false positives from footer link dumps or social icon bars. 

| Criterion  | Rule  | Rationale |
| :---- | ----- | ----- |
| Minimum links  | \> 5 anchor tags inside element  | Distinguishes menus from inline groups |
| Internal ratio  | ≥ 60 % of hrefs share the base domain  | Filters external link lists |
| Depth limit  | Links found within 2 DOM levels of container  | Avoids deep-nested false positives |
| Exclusion list  | Skip elements with class containing footer / breadcrumb / social Precision guard |  |

 

**Pseudo-Logic (Language-Agnostic)** 

`FUNCTION detect_navigation(parsed_html): candidates = parsed_html.find_all(['ul','ol','nav']) FOR each element IN candidates: anchors = element.find_all('a', recursive=depth_limit=2) total_links = COUNT(anchors) internal = COUNT(a WHERE same_domain(a.href, base_url)) IF total_links > 5 AND (internal / total_links) >= 0.6: IF NOT element.has_class(['footer','breadcrumb','social']): tag_element(element, '[NAVIGATION_MENU]') extract_link_labels(anchors)` → `store as menu items RETURN semantic_map`

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 4 

■ **Output Format** 

Each detected menu is serialised as: 

`[NAVIGATION_MENU]` 

`- Home | /index.html` 

`- Shop | /shop/` 

`- About | /about/` 

**1.2 Price Extraction Engine** 

Prices are detected in two passes. Pass A applies a global regular expression across the full page text to identify all currency patterns. Pass B walks up the DOM from each match to find the nearest shared ancestor that groups price, title, and image into a single product unit. 

**Regex Pattern — Pass A** 

`PATTERN = /([£$€`■`¥]\s?\d{1,6}(?:[,\.]\d{2,3})*(?:\.\d{2})?)/g Examples matched: £12.99 $1,299.00 €45` ■`2,500 ¥980 $ 19.95 £ 0.99 €1.200,50` 

**Parent-Element Grouping — Pass B** 

`FUNCTION group_price_context(price_node): ancestor = price_node.parent WHILE ancestor is NOT body: siblings = ancestor.find_all(['img','h1','h2','h3','h4','span','p']) IF has_image(siblings) AND has_text_label(siblings): LABEL ancestor AS '### ITEM POINT' EXTRACT: title` → `first heading or strong text price` → `matched price string image` → `first img[src] cta` → `nearest [ACTION_BUTTON] within ancestor RETURN structured_item ancestor = ancestor.parent` 

■ **Output Format** 

`### ITEM POINT` 

`Title: Classic Running Shoe` 

`[PRICE] £89.99` 

`Image: /media/shoe_01.jpg` 

`[ACTION_BUTTON] Add to Cart | /cart/add?id=42` 

**1.3 Visual Grid Recognition** 

Product or content grids are characterised by a set of sibling elements that share the same HTML tag and exhibit high class-name similarity. The engine uses a **Jaccard similarity score** across tokenised class-name sets to identify these repeated structures without any prior knowledge of the site. 

**Algorithm** 

`FUNCTION detect_grid(parsed_html): FOR each parent IN parsed_html.find_all(): children = parent.direct_children(tag_type='*') IF COUNT(children) < 3: CONTINUE # Group children by tag type tag_groups = GROUP_BY(children, key=child.tag) FOR each group WHERE COUNT >= 3: # Compute pairwise Jaccard similarity of class tokens class_sets = [SET(child.class_tokens) FOR child IN group] avg_jaccard = MEAN(jaccard(a,b) FOR ALL pairs a,b IN class_sets) IF avg_jaccard >= 0.5: LABEL parent AS '[PRODUCT_GRID]' FOR each child IN group: run_price_extraction(child) # nested ITEM POINT run_cta_mapping(child) # nested ACTION_BUTTON RETURN semantic_map`

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 5 

| Minimum siblings  | 3 matching elements (configurable via GRID\_MIN\_ITEMS env var) |
| :---- | :---- |
| **Jaccard threshold**  | 0.5 (configurable via GRID\_JACCARD\_THRESHOLD) |
| **Max scan depth**  | 4 DOM levels from body to avoid O(n²) blowup on deep pages |
| **Nested detection**  | Price \+ CTA passes run automatically inside each grid cell |

**1.4 CTA Button Mapping** 

Call-to-action elements are identified through a keyword match against element text content and ARIA labels. The heuristic targets both \<button\> elements and \<a\> tags styled to look like buttons (detected via class-name patterns). 

| Category  | Keywords Matched (case-insensitive) |
| :---- | :---- |
| Commerce  | buy, add to cart, add to bag, purchase, checkout, order now, get it |
| Signup / Auth  | signup, sign up, register, create account, get started, join free |
| Info / Lead  | learn more, find out, get info, enquire, contact us, book a demo |
| Download  | download, install, get the app, try free, start trial |

`FUNCTION map_cta(element): text_content = LOWERCASE(element.text + element.aria_label) IF ANY(keyword IN text_content FOR keyword IN CTA_KEYWORD_LIST): LABEL element AS '[ACTION_BUTTON]' RECORD: {label: element.text.strip(), href: element.href or '#'} # Fallback: class-name pattern for styled <a> tags IF element.tag == 'a' AND HAS_CLASS(element,` 

`['btn','button','cta','action']): IF element.href IS NOT anchor-only: LABEL element AS '[ACTION_BUTTON]'` 

■ **Output Format** 

`[ACTION_BUTTON] Add to Cart | /cart/add?id=42` 

`[ACTION_BUTTON] Start Free Trial | /signup/` 

`[ACTION_BUTTON] Book a Demo | /demo/`

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 6 

**0**   
**2Semantic Markdown Schema** 

The Semantic Markdown Schema is the contract between the Heuristic Detection Engine and the LLM. It converts raw HTML into a structured, human-readable Markdown document whose sections are labelled with standardised semantic tags. The LLM never sees raw HTML — only this normalised representation. 

**2.1 Complete Tag Reference** 

| Tag  | Meaning  | Source Heuristic  | LLM Usage Hint |
| ----- | ----- | :---- | :---- |
| \[NAVIGATION\_MENU\]  | Top-level site navigation  | Navigation detector  | Answer 'what pages exist?' |
| \[PRICE\]  | Detected currency value  | Price regex pass A  | Answer 'how much is X?' |
| \#\#\# ITEM POINT  | Full product / content unit  | Price pass B grouping  | Answer 'describe item X' |
| \[PRODUCT\_GRID\]  | Collection of similar items  | Grid detector  | Answer 'list all products' |
| \[ACTION\_BUTTON\]  | Clickable call-to-action  | CTA keyword map  | Answer 'how do I buy?' |
| \[PAGE\_TITLE\]  | H1 or \&lt;title\&gt; tag  | Always extracted  | Contextual grounding |
| \[META\_DESC\]  | og:description or meta desc  | Always extracted  | Summary fallback |
| \[BREADCRUMB\]  | Breadcrumb trail text  | Class-name heuristic  | Answer 'where am I?' |
| \[IMAGE\]  | Significant img\[alt\] content  | Alt-text presence check  | Visual context |
| \[FOOTER\]  | Footer link cluster  | Low-position \+ many links  | Legal / contact lookup |

**2.2 Example Semantic Markdown Output** 

`[PAGE_TITLE] Nike Air Max 270 — Official Store [META_DESC] Shop the Nike Air Max 270 in all sizes and colours. Free delivery on orders over £50. [NAVIGATION_MENU] - Men | /men/ - Women | /women/ - Kids | /kids/ - Sale | /sale/ - Find a Store | /stores/ [BREADCRUMB] Home > Men > Shoes > Running [PRODUCT_GRID] ### ITEM POINT Title: Nike Air Max 270 React [PRICE] £129.95 Image: /static/img/am270-react-black.jpg [ACTION_BUTTON] Add to Bag | /cart/add?id=9012 ### ITEM POINT Title: Nike Air Max 270 G Golf Shoe [PRICE] £109.95 Image: /static/img/am270-golf-white.jpg [ACTION_BUTTON] Add to Bag | /cart/add?id=9013 [ACTION_BUTTON] Find Your Size | /size-guide/ [ACTION_BUTTON] Join Nike Membership — Free | /membership/ [FOOTER] - Help | /help/ - Privacy Policy | /privacy/ - Terms of Use | /terms/` 

**2.3 Conversion Pipeline** 

The following sequence transforms a raw HTTP response into a Semantic Markdown string ready for LLM ingestion: 

**1Fetch & Decode**   
HTTP GET → response.text with charset auto-detection (chardet)

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 7 

**2Parse DOM**   
BeautifulSoup(html, 'lxml') — lxml chosen for speed over html.parser 

**3Strip Noise**   
Remove \<script\>, \<style\>, \<noscript\>, hidden elements (display:none) 

**4Run Stage 1–4**   
Execute detect\_navigation → extract\_prices → detect\_grid → map\_cta 

**5Build Semantic Map**   
Merge tagged elements into ordered SemanticMap dataclass 

**6Serialise**   
semantic\_map.to\_markdown() → UTF-8 string for LLM context 

**7Cache**   
Store in Redis with TTL=3600s keyed by URL hash

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 8 

**0**   
**3Backend Integration — views.py & Core** 

**3.1 Structure-Agnostic Prompting** 

The **\_build\_prompt()** function in views.py must be redesigned to be completely blind to the website's domain, category, or purpose. The LLM receives only the Semantic Markdown map and the user's question — no site type, no CSS hints, no domain-specific framing. 

**System Prompt — Universal Version** 

`SYSTEM PROMPT: You are a web intelligence assistant. You will receive a structured "Semantic Markdown Map" generated by analysing a webpage heuristically. The map uses standardised tags: [NAVIGATION_MENU] — site navigation links [PRICE] — detected price values ### ITEM POINT — a complete product or content unit [PRODUCT_GRID] — a collection of similar items [ACTION_BUTTON] — clickable calls to action [PAGE_TITLE] — the page heading [META_DESC] — page meta description [BREADCRUMB] — navigation breadcrumb trail [IMAGE] — image with descriptive alt text Rules: 1. Answer ONLY from information present in the Semantic Map. 2. If the answer cannot be found, say "This information is not available on the current page." 3. Do NOT infer product availability, prices, or links beyond what is explicitly tagged. 4. When listing items, always include their [PRICE] and [ACTION_BUTTON] if present in the same ### ITEM POINT block.` 

**User Turn Template** 

`USER TURN: --- SEMANTIC MAP START --- {semantic_markdown_string} --- SEMANTIC MAP END --- User question: {user_query}` 

**3.2 \_build\_prompt() Implementation Spec** 

| Function signature  | \_build\_prompt(semantic\_map: str, user\_query: str, history: list\[dict\]) → list\[dict\] |
| :---- | ----- |
| **Returns**  | OpenAI-format messages list: \[{role, content}, ...\] |
| **System message**  | Universal system prompt above (stored in prompts/universal\_system.txt) |
| **History truncation**  | Keep last 6 turns maximum; drop oldest pairs first to stay within context budget |
| **Map injection**  | Inject full semantic\_map string into the last user message, wrapped in delimiter tags |
| **Token guard**  | If len(semantic\_map) \> 12,000 tokens → apply  semantic\_map.truncate(priority=\['ITEM POINT','PRICE','NAV'\]) before injection |

**3.3 Context Assembly Flow** 

**1Receive User Query**   
Django view receives POST {url, query, session\_id}

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 9 

**2Check Cache**   
Fetch semantic map from Redis by SHA256(url); if miss → dispatch Celery task 

**3Await Map**   
Poll Redis for up to 30s with 0.5s backoff; return 202 if still processing 

**4Build Messages**   
\_build\_prompt(map, query, session\_history) → messages list 

**5Call LLM**   
openai.chat.completions.create(model, messages, temperature=0.1, max\_tokens=800) 

**6Stream Response**   
Server-Sent Events to frontend; append to session history in Redis

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 10 

**0**   
**4Infrastructure & Performance** 

**4.1 Celery Worker Architecture** 

Heuristic parsing is CPU-bound (DOM traversal \+ regex). All scraping work is offloaded to Celery workers on a dedicated queue, isolating the Python GIL-contention from the async Django request/response cycle. 

**Queue Design** 

| Queue name  | scraper\_heuristic |
| :---- | :---- |
| **Broker**  | Redis (same instance as semantic-map cache, DB 1\) |
| **Worker concurrency**  | 4 processes per worker node (CPU-bound; match to vCPU count) |
| **Task name**  | ai\_engine.tasks.run\_heuristic\_scrape |
| **Task routing**  | All scrape tasks → scraper\_heuristic queue; LLM tasks → llm\_inference queue |
| **Retry policy**  | max\_retries=2, countdown=10s, on: HTTPError, TimeoutError |
| **Result TTL**  | 3600s in Redis result backend; match to semantic map cache TTL |

**Worker Startup Command** 

`celery -A webgpt worker \ --queues=scraper_heuristic \ --concurrency=4 \ --prefetch-multiplier=1 \ --max-tasks-per-child=200 \ --loglevel=info` 

■ **CPU Budget Warning** 

Each heuristic scrape pass may consume 200–600ms of CPU time on large pages (\>500 DOM nodes). Set \--max-tasks-per-child=200 to recycle worker processes and prevent memory leaks from large BeautifulSoup parse trees accumulating across tasks. 

**4.2 CPU Budget & Profiling Targets**

| Metric  | Target (p95)  | Alert Threshold  | Optimisation Lever |
| :---- | :---- | :---- | ----- |
| Full scrape (avg page)  | \< 800ms  | \> 2s  | Increase worker concurrency |
| Navigation detection  | \< 50ms  | \> 200ms  | Limit CSS selector depth |
| Price regex pass  | \< 30ms  | \> 100ms  | Compiled regex, no re-compile per call |
| Grid Jaccard scan  | \< 200ms  | \> 500ms  | Cap DOM scan depth at 4 levels |
| CTA keyword match  | \< 20ms  | \> 80ms  | Pre-tokenise keyword list on startup |
| Redis cache hit rate  | \> 80 %  | \< 60 %  | Increase TTL or add CDN-URL normalisation |

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 11 

**0**   
**5Testing & Validation Framework** 

**5.1 Regression Protocol — books.toscrape.com** 

The legacy bookstore test suite must pass unchanged after the migration. This confirms that the universal heuristics are a strict superset of the old site-specific selectors and have not degraded accuracy on the reference domain. 

| Test ID  | Input URL  | Query  | Expected Semantic Tag  | Pass Condition |
| :---- | ----- | ----- | ----- | ----- |
| REG-01  | /catalogue/  | List all book categories  | \[NAVIGATION\_MENU\]  | ≥ 50 category links detected |
| REG-02  | /catalogue/a-light-in-the-attic\_1000/ What is the price?  |  | \[PRICE\]  | Exact: £51.77 |
| REG-03  | /catalogue/page-2.html  | How many books on this page? \[PRODUCT\_GRID\]  |  | 20 ITEM POINTs detected |
| REG-04  | /catalogue/  | Add first book to basket  | \[ACTION\_BUTTON\]  | Action button found on ITEM POINT |
| REG-05  | /catalogue/  | What is the most expensive book?\[PRICE\] sort  |  | Correct title \+ price returned by LLM |

**5.2 Cross-Domain Benchmark Sites** 

Each benchmark site represents a different structural pattern the universal engine must handle: 

| Site Type  | Example URL  | Key Heuristic Challenge  | Validation Query |
| :---- | :---- | ----- | ----- |
| E-commerce (large)  | nike.com/gb/w/mens-shoes  | React-rendered grid; lazy-loaded pricesWhat colours are available for Air Max 270? |  |
| Local business  | village-bakery.co.uk  | No product grid; prices in prose  | What is the price of a sourdough loaf? |
| SaaS landing page  | notion.so/product  | Multiple CTAs; no prices  | How do I sign up for a free trial? |
| Blog / editorial  | theguardian.com  | Articles not products; no prices  | What are the navigation sections? |
| Marketplace listing  | ebay.co.uk/itm/123  | Auction price; bid button as CTA  | What is the current bid price? |

**5.3 Logic Verification Query Bank** 

 

 

 

 

 

 

 

 

These standardised questions are run against every benchmark site after scraping. Acceptable answers are evaluated by the QA agent against the ground-truth Semantic Map to compute precision and recall scores. 

| QID  | Query  | Tag Exercised  | Acceptable Answer Criteria |
| :---- | ----- | :---- | ----- |
| LV-01  | What are the navigation options on this page? \[NAVIGATION\_MENU\]  |  | All detected menu links present; no hallucinated links |
| LV-02  | What is the most expensive item on this page? \[PRICE\] \+ sort  |  | Correct item title \+ highest price value |
| LV-03  | What is the cheapest item on this page? \[PRICE\] \+ sort  |  | Correct item title \+ lowest price value |
| LV-04  | List all products visible on this page.  | \[PRODUCT\_GRID\]  | Count matches detected ITEM POINTs ± 1 |
| LV-05  | How do I purchase the first product?  | \[ACTION\_BUTTON\]  | Correct CTA label \+ URL fragment |
| LV-06  | What is this page about?  |  | \[PAGE\_TITLE\] \+ \[META\_DESC\] Answer grounded in title or meta description |

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 12 

| LV-07  | Is there a sign-up or registration option? \[ACTION\_BUTTON\]  |  | Accurate yes/no \+ button label if present |
| :---- | ----: | :---- | :---- |
| LV-08  | Where can I find help or contact information? \[FOOTER\]  |  | Footer links referenced; no invented URLs |

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project  
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 13 

**0**   
**6Step-by-Step Implementation Guide** 

■ **Agent Instructions** 

This section is the authoritative runbook for the Antigravity autonomous coding agent. Execute each phase in sequence. Do **not** begin a phase until all acceptance criteria of the previous phase are verified. 

**PHASE A: Environment Preparation** 

| A-1 Dependency audit  Verify beautifulsoup4≥4.12, lxml, redis-py, celery≥5.3 in requirements.txt. Add chardet if missing. |
| ----- |
| **A-2 Config variables**  Add to settings.py: GRID\_MIN\_ITEMS=3, GRID\_JACCARD\_THRESHOLD=0.5,  SCRAPE\_MAX\_DEPTH=4, SEMANTIC\_MAP\_TTL=3600, SCRAPER\_QUEUE='scraper\_heuristic'. |
| **A-3 Prompt file**  Create prompts/universal\_system.txt with the system prompt from Section 3.1. |

**PHASE B: Heuristic Engine — scraper.py** 

| B-1 SemanticMap dataclass  Define dataclass with fields: navigation, items, grid\_groups, cta\_buttons, page\_title, meta\_desc, breadcrumb. Add to\_markdown() method. |
| ----- |
| **B-2 detect\_navigation()**  Implement per Section 1.1 spec. Unit test against ≥3 static HTML fixtures covering: standard nav, footer-only, deep-nested links. |
| **B-3 extract\_prices()**  Implement Pass A regex (compile once at module level). Implement Pass B ancestor walk. Unit test currency formats: £, $, €, ■, ¥, comma-separated thousands. |
| **B-4 detect\_grid()**  Implement Jaccard scorer. Unit test with a 3-item, 5-item, and 20-item product grid fixture. Verify ITEM POINT nested detection fires correctly. |
| **B-5 map\_cta()**  Implement keyword matcher \+ class-name fallback. Unit test against button, anchor-as-button, aria-label variants. |
| **B-6 run\_heuristic\_scrape()**  Compose all four functions. Serialise to SemanticMap. Cache result in Redis. Register as Celery task. |

**PHASE C: Backend Integration — views.py**

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 14 

| C-1 \_build\_prompt()  Refactor to structure-agnostic version per Section 3.1–3.2. Remove all bookstore-specific framing. Add history truncation (max 6 turns). Add token guard. |
| :---- |
| **C-2 Scrape dispatch view**  Create /api/scrape/ endpoint: accepts {url}, dispatches Celery task, returns {task\_id}. Create /api/scrape/status/?task\_id={id} polling endpoint. |
| **C-3 Chat view**  Update /api/chat/ to: fetch semantic map from Redis, call \_build\_prompt(), stream LLM response via SSE. |

**PHASE D: Celery Configuration** 

| D-1 celery\_config.py  Define task\_routes: {'ai\_engine.tasks.run\_heuristic\_scrape': {'queue': 'scraper\_heuristic'}}. Set worker\_prefetch\_multiplier=1, task\_acks\_late=True. |
| :---- |
| **D-2 Worker deploy**  Update Procfile / docker-compose.yml with worker command from Section 4.1. Ensure  CELERY\_BROKER\_URL and CELERY\_RESULT\_BACKEND point to Redis DB 1\. |

**PHASE E: Testing & Sign-Off**

| E-1 Unit tests  All module-level unit tests (Phases B, C) must pass. Target: 100% coverage on heuristic functions. |
| ----- |
| **E-2 Regression suite**  Run REG-01 through REG-05 (Section 5.1). All must pass before proceeding. |
| **E-3 Cross-domain suite**  Run all benchmark sites (Section 5.2). Document precision/recall per site. |
| **E-4 Logic query bank**  Run LV-01 through LV-08 on ≥2 benchmark sites. Minimum acceptable score: 6/8 per site. |
| **E-5 Performance check**  Run Locust load test: 10 concurrent scrape requests. Verify p95 ≤ 800ms per Section 4.2. |
| **E-6 Final approval**  Present benchmark results to project lead. Await explicit approval before merging to main. |

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project   
**Web-GPT · Universal Semantic Scraper · Technical Specification v1.0** Page 15 

**0**   
**7Open Questions & Risk Register** 

| Risk ID  | Description  | Likelihood  | Impact  | Mitigation |
| ----- | ----- | ----- | :---- | ----- |
| R-01  |  |  |  | JavaScript-rendered pages: heuristics run on server HTML; SPAs may return near-empty DOM. High High Integrate Playwright/Puppeteer as a fallback fetch layer with JS execution. |
| R-02  |  |  |  | False-positive navigation: footer link dumps classified as nav menus. Medium Low Exclusion list (Section 1.1) \+ vertical-position check (top 20% of page). |
| R-03  | Non-Latin currency symbols missed by regex. Low  |  | Medium  | Extend regex to include: kr, CHF, R$, AED, SGD, AUD symbol variants. |
| R-04  | Celery worker overload during scrape spikes. Medium  |  | Medium  | Auto-scaling worker group; circuit breaker returning cached stale maps. |
| R-05  | LLM context overflow on pages with 100+ products. Medium  |  | High  | Semantic map truncation per Section 3.2 token guard; paginate product gri |
| R-06  | robots.txt / rate-limit blocks on cross-domain test sites. High Low  |  |  | Use official scraping-sandbox sites for CI; cache real-site results for demo  |

 

 

 

 

**Open Design Questions** 

The following decisions require project-lead input before implementation begins: 

| OQ  JavaScript rendering  1  Should the first version support JS-rendered SPAs via Playwright, or ship with HTML-only support and add Playwright in v1.1? JS support adds \~400ms per scrape but dramatically improves coverage of modern e-commerce sites. |
| :---- |
| **OQ  Confidence scoring  2**  Should the SemanticMap expose a per-tag confidence score (e.g., nav\_confidence: 0.87) so the LLM can hedge its answers? Adds complexity but improves answer calibration. |
| **OQ  Multi-page scraping  3**  Should the scraper follow pagination links (\[NAVIGATION\_MENU\] with 'Next Page') automatically up to a configurable depth, or remain single-page only? |
| **OQ  User feedback loop  4**  Should incorrect answers trigger a re-scrape with adjusted heuristic thresholds, or is manual threshold tuning via environment variables sufficient for v1? |

✓ **Approval Gate** 

This document constitutes the complete technical specification for the Web-GPT Universal Heuristic Scraper upgrade. Implementation by the Antigravity agent should not begin until this document has been reviewed and approved by the project lead. Please respond with **APPROVED** or submit change requests against specific section numbers.

CONFIDENTIAL · For internal use by the Antigravity Agent © 2025 Web-GPT Project 