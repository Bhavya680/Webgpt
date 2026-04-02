import time
from celery import shared_task
from core.models import Bot, TrainingStatus, ScrapedPage

@shared_task
def train_bot_task(bot_id, website_url):
    print(f"[CELERY] Scraping started for Bot {bot_id} at {website_url}")
    
    try:
        bot = Bot.objects.get(id=bot_id)
        status = bot.training_status
    except Bot.DoesNotExist:
        print(f"[CELERY] Error: Bot {bot_id} not found.")
        return

    # Phase 1: Simulate discovery
    status.status_message = "Found sitemap.xml... crawling base URL."
    status.total_pages = 1
    status.save()
    time.sleep(1)
    
    # Phase 2: Actual Scraping
    print(f"[CELERY] Actually scraping {website_url}...")

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
        crawl_limit = 5
        
        status.total_pages = crawl_limit
        status.save()

        total_chunks = 0
        pages_processed = 0

        while queue and pages_processed < crawl_limit:
            current_url = queue.pop(0)
            
            if current_url in visited:
                continue
            
            visited.add(current_url)
            pages_processed += 1
            
            status.status_message = f"Crawling page {pages_processed}/{crawl_limit}..."
            status.pages_scraped = pages_processed
            status.save()
            print(f"[CELERY] Scraping {current_url}...")

            try:
                text, links = scrape_url(current_url)
                
                # Append newly discovered links to the end of the queue
                for link in links:
                    if link not in visited and link not in queue:
                        queue.append(link)
                
                status.status_message = f"Embedding {current_url}..."
                status.save()
                
                # Embed the text and retrieve chunk metric
                chunks_created = embed_and_store(text, str(bot.bot_id), source_url=current_url)
                total_chunks += chunks_created
                
                # Save into the real database
                from core.models import ScrapedPage
                ScrapedPage.objects.create(
                    bot=bot,
                    url=current_url,
                    status='success',
                    chunks_count=chunks_created
                )
                
            except Exception as page_err:
                print(f"[CELERY] Failed to scrape {current_url}: {page_err}")
                from core.models import ScrapedPage
                ScrapedPage.objects.create(
                    bot=bot,
                    url=current_url,
                    status='failed',
                    chunks_count=0
                )

        status.chunks_created = total_chunks
        status.save()
        print(f"[CELERY] Crawl complete. Processed {pages_processed} pages with {total_chunks} total chunks.")

    except Exception as e:
        print(f"[CELERY] Error during real scraping: {e}")
        bot.status = 'failed'
        bot.save()
        status.status_message = f"Extraction failed: {str(e)}"
        status.save()
        return

    time.sleep(1) # Artificial delay for UI updates

    # Mark as complete
    bot.status = 'active'
    bot.save()
    
    status.status_message = "Knowledge extraction successful."
    status.save()
    
    print("[CELERY] Training Complete.")
