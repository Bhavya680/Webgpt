from core.models import Bot, ScrapedPage
bots = Bot.objects.filter(pages__isnull=True).distinct()
for bot in bots:
    print(f"Creating pages for {bot.name}")
    for i in range(1, 6):
        page_url = f"{bot.url}/page-{i}" if not bot.url.endswith('/') else f"{bot.url}page-{i}"
        ScrapedPage.objects.create(bot=bot, url=page_url, status='success')

print("Complete.")
