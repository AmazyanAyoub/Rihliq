# ══════════════════════════════════════════════════════════
# Timeout overrides - MUST be set BEFORE browser_use import
# ══════════════════════════════════════════════════════════
import os
os.environ["TIMEOUT_NavigateToUrlEvent"] = "60.0"
os.environ["TIMEOUT_BrowserStateRequestEvent"] = "90.0"
os.environ["TIMEOUT_ScreenshotEvent"] = "60.0"
os.environ["TIMEOUT_TypeTextEvent"] = "120.0"
# ══════════════════════════════════════════════════════════

from browser_use import Agent, Browser, ChatOllama
from dotenv import load_dotenv

load_dotenv()

# ── Ollama vision model (browser-use wrapper) ─────────────
model = ChatOllama(
    model="qwen3-vl:8b",              # 👈 your vision model
    host="http://localhost:11434",     # browser-use uses `host` not `base_url`
)

# ── Webshare proxy ────────────────────────────────────────
PROXY = {
    "server": f"http://{os.getenv('PROXY_HOST')}:{os.getenv('PROXY_PORT')}",
    "username": os.getenv("PROXY_USERNAME"),
    "password": os.getenv("PROXY_PASSWORD"),
}


async def smart_scrape(query: str, url: str) -> str:
    browser = Browser(
        headless=False,
        proxy=PROXY,
    )

    task = f"""
You are a web scraping agent. Your ONLY job is to extract data from ONE specific page.

TARGET URL (THE ONLY PAGE YOU ARE ALLOWED TO BE ON):
{url}

═══════════════════════════════════════════════════════════
🔒 HARD RULES
═══════════════════════════════════════════════════════════
1. STAY on the TARGET URL. NEVER navigate away.
2. NEVER click links to other pages.
3. NEVER use search engines.
4. If the page is slow or shows skeleton loaders (gray placeholder boxes), WAIT using the `wait` action for 5 seconds before acting.
5. NEVER scroll if the page hasn't finished loading. Check for skeleton placeholders first.

═══════════════════════════════════════════════════════════
⏳ HANDLING SLOW LOADS
═══════════════════════════════════════════════════════════
- If you see skeleton/shimmer/placeholder boxes, content is still loading.
- Use the `wait` action for 5 seconds, then check again.
- Only scroll and extract once REAL content is visible.
- Repeat waits if needed (up to 3 times) until real content appears.

═══════════════════════════════════════════════════════════
✅ ALLOWED ACTIONS
═══════════════════════════════════════════════════════════
- `wait` (5 seconds when page is loading)
- Scroll the current page (1 page at a time)
- Close cookie banners
- Click accordions ("En savoir plus", "Voir plus", "+") that expand in-place
- Click tabs that reveal content on the same page
- Use extract action to pull data

═══════════════════════════════════════════════════════════
📋 USER QUERY
═══════════════════════════════════════════════════════════
{query}

═══════════════════════════════════════════════════════════
🎯 WORKFLOW
═══════════════════════════════════════════════════════════
1. Verify you are on {url}
2. If skeleton loaders are visible → wait 5s, repeat until real content shows
3. Close cookie banner if present
4. Scroll slowly top to bottom (1 page at a time)
5. Expand collapsed sections as you see them
6. Use extract to gather all data
7. Return JSON and stop

═══════════════════════════════════════════════════════════
📤 OUTPUT
═══════════════════════════════════════════════════════════
- Pure JSON. No markdown. No explanations.
- Use null for missing fields.
- Only return data actually visible.
"""

    agent = Agent(
        task=task,
        llm=model,
        browser=browser,
        use_vision=False,
        max_actions_per_step=1,
        step_timeout=300,
        llm_timeout=240,
    )

    try:
        history = await agent.run(max_steps=25)
        return history.final_result()
    finally:
        try:
            await browser.kill()
        except Exception:
            pass