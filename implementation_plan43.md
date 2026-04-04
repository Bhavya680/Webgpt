# Implementation Plan - Universal Semantic Scraper (Web-GPT)

This plan moves our RAG pipeline from "Site-Specific" to "Universal Architecture," allowing it to handle any store, landing page, or blog without changing a single line of code.

## User Review Required
> [!IMPORTANT]
> **Heuristic Logic vs Selective Scraping**: We are moving away from selectors like `div.side_categories` and replacing them with **Heuristics (Pattern Recognition)**. The scraper will now "Guess" what a product or a category is based on the website's visual structure.

## Proposed Changes

### [ai_engine]

#### [NEW] [Universal Heuristic Scraper](file:///c:/Users/Admin/Desktop/Webgpt/ai_engine/scraper.py)
I will replace the bookstore-specific logic with a **Pattern-Matching Engine**:

1. **Category Detection**:
   - Instead of looking for `side_categories`, we look for any `<ul>` or `<nav>` that contains more than 5 internal links. We label these as: `[NAVIGATION_MENU]`.
2. **Price Point Detection**:
   - Use Regex (e.g., `/([£$€₹]\s?\d+(?:\.\d{2})?)/g`) to find **any** currency pattern on the page. If found, we look at the parent element and label everything in that group as: `### ITEM POINT`.
3. **Data Grid Detection**:
   - Detect "Repeated Structures" (Sibling elements with the same tag and similar class names). This is how the bot identifies a "Product Grid" automatically on any site.
4. **Call to Action Detection**:
   - Identify buttons or large links with text like "Buy," "Cart," "Signup," or "Info" and label them as `[ACTION_BUTTON]`.

#### [MODIFY] [views.py](file:///c:/Users/Admin/Desktop/Webgpt/core/views.py)
- **Structure-Agnostic Prompt**: I will update `_build_prompt` to be "blind" to the website's type.
- Example: "Use the provided Semantic Markdown map to answer questions. Look for tags like [PRICE], [MENU], and [ACTION] to guide your answers."

## Verification Plan

### Automated/Manual Testing
1. **Regression Check**: Re-train the bot on `books.toscrape.com`. It should still find prices and categories using the new universal logic.
2. **Cross-Domain Test**: I will ask you to test it on a **completely different site** (e.g., a Nike product page or a local bakery landing page). 
3. **Universal Logic Check**: Ask: *"What are the navigation options?"* and *"What is the most expensive thing on this page?"*

## Open Questions
> [!WARNING]
> **Performance**: Heuristic scraping is slightly more CPU-intensive for the Python worker. However, since we are doing this in the background with Celery, it shouldn't affect the user experience.

**Shall I wait for your final approval before implementing this Universal "Web-GPT" version?**
