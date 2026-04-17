import os
import json
import asyncio
import httpx
from dotenv import load_dotenv

# Load env from root
load_dotenv(dotenv_path="../.env")

# --- Config ---
DUFFEL_ACCESS_TOKEN = os.getenv("DUFFEL_ACCESS_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

DEBUG_DIR = "debug_responses"
os.makedirs(DEBUG_DIR, exist_ok=True)

async def capture_flights():
    print("Capturing Flights (Duffel)...")
    url = "https://api.duffel.com/air/offer_requests"
    headers = {
        "Authorization": f"Bearer {DUFFEL_ACCESS_TOKEN}",
        "Duffel-Version": "v2",
        "Content-Type": "application/json"
    }
    payload = {
        "data": {
            "slices": [
                {"origin": "LHR", "destination": "CDG", "departure_date": "2026-06-15"}
            ],
            "passengers": [{"type": "adult"}],
            "cabin_class": "economy"
        }
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create offer request
        res = await client.post(url, headers=headers, json=payload)
        offer_request = res.json()
        with open(f"{DEBUG_DIR}/duffel_offer_request.json", "w") as f:
            json.dump(offer_request, f, indent=2)
        
        offer_request_id = offer_request["data"]["id"]
        
        # Get offers
        res = await client.get(
            "https://api.duffel.com/air/offers",
            headers=headers,
            params={"offer_request_id": offer_request_id, "limit": 5}
        )
        offers = res.json()
        with open(f"{DEBUG_DIR}/duffel_offers.json", "w") as f:
            json.dump(offers, f, indent=2)
    print("  Done.")

async def capture_hotels():
    print("Capturing Hotels (Booking.com via RapidAPI)...")
    headers = {
        "x-rapidapi-host": "booking-com.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Resolve destination
        res = await client.get(
            "https://booking-com.p.rapidapi.com/v1/hotels/locations",
            headers=headers,
            params={"name": "Paris", "locale": "en-gb"}
        )
        locations = res.json()
        with open(f"{DEBUG_DIR}/booking_locations.json", "w") as f:
            json.dump(locations, f, indent=2)
            
        dest_id = locations[0]["dest_id"]
        dest_type = locations[0]["dest_type"]

        # Search
        res = await client.get(
            "https://booking-com.p.rapidapi.com/v1/hotels/search",
            headers=headers,
            params={
                "dest_id": dest_id,
                "dest_type": dest_type,
                "checkin_date": "2026-06-15",
                "checkout_date": "2026-06-20",
                "adults_number": "2",
                "room_number": "1",
                "order_by": "popularity",
                "locale": "en-gb",
                "filter_by_currency": "USD",
                "units": "metric",
                "page_number": "0"
            }
        )
        hotels = res.json()
        with open(f"{DEBUG_DIR}/booking_search.json", "w") as f:
            json.dump(hotels, f, indent=2)
    print("  Done.")

async def capture_restaurants():
    print("Capturing Restaurants (Google Places New)...")
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "*" # Request EVERYTHING for schema analysis
    }
    payload = {
        "textQuery": "Top restaurants in Paris",
        "maxResultCount": 5
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(url, headers=headers, json=payload)
        restaurants = res.json()
        with open(f"{DEBUG_DIR}/google_restaurants.json", "w") as f:
            json.dump(restaurants, f, indent=2)
    print("  Done.")

async def main():
    tasks = []
    if DUFFEL_ACCESS_TOKEN: tasks.append(capture_flights())
    if RAPIDAPI_KEY: tasks.append(capture_hotels())
    if GOOGLE_MAPS_API_KEY: tasks.append(capture_restaurants())
    
    if not tasks:
        print("No API keys found in .env!")
        return
        
    await asyncio.gather(*tasks)
    print(f"\nAll raw responses saved to {DEBUG_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
