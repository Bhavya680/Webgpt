import os
import django
import sys

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webbot.settings')
django.setup()

from core.models import Bot
from core.views import _retrieve_context, _build_prompt, _call_colab_api

def chat_loop():
    print("=========================================")
    print("   🤖 SITEBOT AI TERMINAL CHAT DEBUGGER  ")
    print("=========================================")
    
    # Get the latest active bot
    bot = Bot.objects.filter(status='active').order_by('-created_at').first()
    
    if not bot:
        print("[!] No 'active' bots found. Please go to the dashboard and create/train one first.")
        sys.exit(1)
        
    print(f"\n[*] Using Bot: {bot.name}")
    print(f"[*] Scraped URL: {bot.url}")
    print(f"[*] Bot UUID: {bot.bot_id}")
    
    print("\n[i] Type 'exit' or 'quit' to end the chat.")
    print("-----------------------------------------")
    
    while True:
        try:
            message = input("\n👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break
            
        if message.lower() in ['exit', 'quit']:
            print("Exiting...")
            break
            
        if not message:
            continue
            
        print("\n[⚙] Searching local ChromaDB for context...")
        chunks = _retrieve_context(message, str(bot.bot_id))
        
        if not chunks:
            print("[!] No relevant chunks found in the database. LLM context will be empty.")
            
        print(f"[⚙] Formulating prompt with {len(chunks)} context chunks...")
        prompt = _build_prompt(message, chunks)
        
        print(f"[⚙] Sending request to Colab API (ngrok)...")
        answer, status = _call_colab_api(prompt)
        
        print("\n🤖 Bot:")
        print(f"{answer}")
        print(f"\n(API Status: {status})")

if __name__ == "__main__":
    chat_loop()
