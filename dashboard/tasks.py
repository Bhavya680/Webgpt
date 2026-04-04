import time
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
from celery import shared_task
from django.utils import timezone
from core.models import Bot, TrainingStatus, ScrapedPage


# ── Configuration ──────────────────────────────────────────────────
CRAWL_LIMIT = 50  # Max pages to scrape per bot

# File extensions to skip (non-content resources)
SKIP_EXTENSIONS = {
    '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp',
    '.zip', '.tar', '.gz', '.rar',
    '.css', '.js', '.woff', '.woff2', '.ttf', '.eot',
    '.mp3', '.mp4', '.wav', '.avi', '.mov',
    '.xml', '.json', '.rss',
}


def _normalize_url(url: str) -> str:
    """Normalize a URL for deduplication.
    
    - Strips trailing slashes
    - Strips fragments (#...)
    - Sorts query parameters
    - Lowercases scheme and netloc
    """
    parsed = urlparse(url)
    # Lowercase scheme and netloc
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    # Strip trailing slash from path (except root '/')
    path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
    # Sort query params
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    sorted_query = urlencode(sorted(query_params.items()), doseq=True)
    # Rebuild without fragment
    return urlunparse((scheme, netloc, path, parsed.params, sorted_query, ''))


def _should_skip_url(url: str) -> bool:
    """Check if URL should be skipped (non-content resources)."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    return any(path.endswith(ext) for ext in SKIP_EXTENSIONS)


@shared_task
def train_bot_task(bot_id, website_url):
    print(f"[CELERY] Scraping started for Bot {bot_id} at {website_url}")
    
    try:
        bot = Bot.objects.get(id=bot_id)
        status = bot.training_status
    except Bot.DoesNotExist:
        print(f"[CELERY] Error: Bot {bot_id} not found.")
        return

    # Phase 1: Initialization
    status.status_message = "Initializing universal scraper engine..."
    status.total_pages = 1
    status.save()
    time.sleep(0.5)
    
    # Phase 2: Actual Scraping with Universal Heuristic Engine
    print(f"[CELERY] Starting universal heuristic scrape of {website_url}...")

    try:
        from ai_engine.scraper import scrape_url
        from ai_engine.embedder import embed_and_store, clear_collection

        # Reset bot's existing pages in DB and ChromaDB
        bot.pages.all().delete()
        clear_collection(str(bot.bot_id))

        status.status_message = "Starting neural crawler..."
        status.save()

        visited = set()
        queue = [website_url]
        
        # Set total_pages to crawl limit initially, will adjust as we discover pages
        status.total_pages = CRAWL_LIMIT
        status.save()

        total_chunks = 0
        pages_processed = 0
        pages_failed = 0

        while queue and pages_processed < CRAWL_LIMIT:
            current_url = queue.pop(0)
            
            # Normalize for dedup check
            normalized = _normalize_url(current_url)
            if normalized in visited:
                continue
            
            # Skip non-content URLs
            if _should_skip_url(current_url):
                continue
            
            visited.add(normalized)
            pages_processed += 1
            
            # Update status (batch: every 3 pages to reduce DB writes)
            if pages_processed % 3 == 1 or pages_processed <= 3:
                status.status_message = f"Crawling page {pages_processed}/{min(CRAWL_LIMIT, pages_processed + len(queue))}..."
                status.pages_scraped = pages_processed
                status.save()
            
            print(f"[CELERY] [{pages_processed}/{CRAWL_LIMIT}] Scraping {current_url}...")

            try:
                text, links = scrape_url(current_url)
                
                # Append newly discovered links to the end of the queue
                for link in links:
                    norm_link = _normalize_url(link)
                    if norm_link not in visited and not _should_skip_url(link):
                        # Check if link is already queued (use normalized form)
                        already_queued = any(
                            _normalize_url(q) == norm_link for q in queue
                        )
                        if not already_queued:
                            queue.append(link)
                
                # Embed the semantic markdown
                status.status_message = f"Embedding page {pages_processed}..."
                if pages_processed % 3 == 0:
                    status.save()
                
                chunks_created = embed_and_store(text, str(bot.bot_id), source_url=current_url)
                total_chunks += chunks_created
                
                # Save to database
                ScrapedPage.objects.create(
                    bot=bot,
                    url=current_url,
                    status='success',
                    chunks_count=chunks_created
                )
                
            except Exception as page_err:
                pages_failed += 1
                print(f"[CELERY] Failed to scrape {current_url}: {page_err}")
                ScrapedPage.objects.create(
                    bot=bot,
                    url=current_url,
                    status='failed',
                    chunks_count=0
                )

        # Final status update
        status.pages_scraped = pages_processed
        status.chunks_created = total_chunks
        status.total_pages = pages_processed
        status.save()
        print(f"[CELERY] Crawl complete. Processed {pages_processed} pages "
              f"({pages_failed} failed) with {total_chunks} total chunks.")

    except Exception as e:
        print(f"[CELERY] Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        bot.status = 'failed'
        bot.save()
        status.status_message = f"Extraction failed: {str(e)}"
        status.save()
        return

    time.sleep(0.5)

    # Mark as complete
    bot.status = 'active'
    bot.save()
    
    status.status_message = "Knowledge extraction successful."
    status.completed_at = timezone.now()
    status.save()
    
    print("[CELERY] Training Complete.")
