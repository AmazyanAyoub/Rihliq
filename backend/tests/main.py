# import asyncio
# from agent_scraper import smart_scrape


# async def main():
#     # ── Define what you want ──────────────────────────────
#     query = "Find the cheapest round-trip flight from Casablanca to Paris departing May 10 2026, returning May 17 2026. Return departure time, arrival time, airline, price, number of stops, and total duration."
#     url   = "https://www.google.com/travel/flights"

#     # ── Run the agent ─────────────────────────────────────
#     print("🤖 Starting agent...")
#     print(f"📍 URL:   {url}")
#     print(f"❓ Query: {query}\n")

#     result = await smart_scrape(query=query, url=url)

#     print("\n" + "=" * 60)
#     print("RESULT:")
#     print("=" * 60)
#     print(result)


# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
from agent_scraper import smart_scrape


async def main():
    query = """
Extract ALL information about every product on this page. For each product, capture:

- Product name
- Full description
- Price (and any discount/original price)
- Available sizes / weights / variants
- Key benefits (bénéfices) — every single one listed
- Product details / characteristics (caractéristiques)
- Nutritional information (informations nutritionnelles) — all values
- Ingredients / composition if shown
- Feeding guidelines / recommended daily amount if shown
- Customer reviews (avis) — rating, number of reviews, and individual review text if visible
- Product image URLs
- Product page URL
- Any tags or labels (e.g. "Nouveau", "Promo", "Bestseller")

Scroll down through the ENTIRE page to make sure nothing is missed. Expand any collapsible sections (accordions, "Voir plus", "En savoir plus" buttons). Check all tabs if there are tabs.

Return a JSON array where each element is one product with all the fields above. Use null for missing fields.
"""

    url = "https://www.royalcanin.com/fr/dogs/products/retail-products/puppy---mini-3000"

    print("🤖 Starting scraper...")
    print(f"📍 URL:   {url}\n")

    result = await smart_scrape(query=query, url=url)

    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())