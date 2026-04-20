from browser_use import Agent, Browser, ChatGroq
from dotenv import load_dotenv
import os

load_dotenv()

# ── Groq vision model (built into browser-use) ───────────
model = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
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
You are a web scraping agent. Your goal is to extract structured data from a website.

TARGET URL: {url}

USER QUERY: {query}

INSTRUCTIONS:
1. Navigate to the target URL.
2. If there's a cookie banner, close/accept it.
3. Understand the page and figure out what the user wants.
4. Interact with the page as needed (fill forms, click buttons, scroll, paginate) to find the requested data.
5. Extract ALL matching items from the results.
6. Return the data as a clean JSON array of objects.
7. Each object should have all relevant fields depending on the query.

IMPORTANT:
- Do NOT invent data. Only return what is actually visible on the page.
- If the page is empty or nothing matches, return an empty array [].
- Your final output MUST be valid JSON only. No explanations, no markdown fences.
"""

    agent = Agent(
        task=task,
        llm=model,
        browser=browser,
        use_vision=True,
    )

    try:
        history = await agent.run()
        return history.final_result()
    finally:
        # Browser session auto-closes, but force it just in case
        try:
            await browser.kill()
        except Exception:
            pass