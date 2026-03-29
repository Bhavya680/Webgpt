import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""Quick smoke test for scraper.py — no network required."""
from scraper import extract_clean_text, save_text, OUTPUT_FILE

HTML = """
<html>
<head><script>var x = 1;</script><style>body{color:red}</style></head>
<body>
  <nav><a href="/">Home</a><a href="/about">About</a></nav>
  <header><h1>Site Banner</h1></header>
  <main>
    <h1>Main Title</h1>
    <h2>Subtitle About the Topic</h2>
    <p>This is the first real paragraph with meaningful content.</p>
    <p>Here is another paragraph with more details.</p>
    <div>This div text should NOT appear.</div>
    <span>Span text should NOT appear either.</span>
    <h3>Section Three Heading</h3>
    <p>Final paragraph of the article.</p>
  </main>
  <footer><p>Copyright 2026</p></footer>
  <aside>Sidebar junk</aside>
</body>
</html>
"""

text = extract_clean_text(HTML)
save_text(text, OUTPUT_FILE)

print("=== EXTRACTED TEXT ===")
print(text)
print("=====================")
print(f"\nSaved to: {OUTPUT_FILE}")

