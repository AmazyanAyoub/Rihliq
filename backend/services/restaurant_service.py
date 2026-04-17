import logging
from typing import List

import httpx

from config import settings
from models.schemas import Restaurant, RestaurantSearchRequest

logger = logging.getLogger(__name__)

# ── Google Places API (New) — Text Search ─────────────────────────────
PLACES_BASE_URL = "https://places.googleapis.com/v1/places:searchText"

# Google price_level enum → symbol
# New API returns: PRICE_LEVEL_FREE, PRICE_LEVEL_INEXPENSIVE,
# PRICE_LEVEL_MODERATE, PRICE_LEVEL_EXPENSIVE, PRICE_LEVEL_VERY_EXPENSIVE
PRICE_MAP = {
    "PRICE_LEVEL_FREE":           "$",
    "PRICE_LEVEL_INEXPENSIVE":    "$",
    "PRICE_LEVEL_MODERATE":       "$$",
    "PRICE_LEVEL_EXPENSIVE":      "$$$",
    "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
}


async def search_restaurants(request: RestaurantSearchRequest) -> List[Restaurant]:
    if not settings.google_maps_api_key:
        logger.warning("Google Maps API key not set — returning mock restaurants")
        return _mock_restaurants(request)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            search_query = f"{request.query} restaurants in {request.destination}"

            res = await client.post(
                PLACES_BASE_URL,
                headers={
                    "Content-Type":    "application/json",
                    "X-Goog-Api-Key":  settings.google_maps_api_key,
                    # FieldMask controls what data comes back AND what you're billed for.
                    # Only request fields you actually need!
                    "X-Goog-FieldMask": ",".join([
                        "places.id",
                        "places.displayName",
                        "places.formattedAddress",
                        "places.location",
                        "places.rating",
                        "places.userRatingCount",
                        "places.priceLevel",
                        "places.primaryType",
                        "places.primaryTypeDisplayName",
                        "places.currentOpeningHours",
                        "places.regularOpeningHours",
                        "places.websiteUri",
                        "places.nationalPhoneNumber",
                        "places.photos",
                    ]),
                },
                json={
                    "textQuery":      search_query,
                    "maxResultCount": request.limit,
                    "languageCode":   "en",
                },
            )
            res.raise_for_status()
            payload = res.json()

            # Debug: uncomment to see raw response
            # import json
            # print(json.dumps(payload, indent=2))

            results = payload.get("places", [])
            logger.info(f"[RESTAURANT] Found {len(results)} places")

        restaurants: List[Restaurant] = []
        for place in results:
            # --- ID ---
            place_id = place.get("id", "")

            # --- Name ---
            display_name = place.get("displayName", {})
            name = display_name.get("text", "Unknown") if isinstance(display_name, dict) else str(display_name)

            # --- Cuisine ---
            cuisine = None
            primary_type_display = place.get("primaryTypeDisplayName", {})
            if isinstance(primary_type_display, dict):
                cuisine = primary_type_display.get("text")
            if not cuisine:
                cuisine = place.get("primaryType", "Restaurant").replace("_", " ").title()

            # --- Photos ---
            photos_list = place.get("photos", [])
            photos = []
            if photos_list:
                photo_name = photos_list[0].get("name", "")
                if photo_name:
                    photo_url = (
                        f"https://places.googleapis.com/v1/{photo_name}/media"
                        f"?maxHeightPx=400&key={settings.google_maps_api_key}"
                    )
                    photos.append(photo_url)

            restaurants.append(Restaurant(
                id=place_id,
                name=name,
                cuisine=cuisine,
                rating=float(place.get("rating", 0.0)),
                user_rating_count=place.get("userRatingCount"),
                price_range=PRICE_MAP.get(place.get("priceLevel"), "$$"),
                location={
                    "latitude": place.get("location", {}).get("latitude"),
                    "longitude": place.get("location", {}).get("longitude"),
                    "address": place.get("formattedAddress"),
                    "city": request.destination
                },
                opening_hours=None, # Already handled complexly below if needed
                description=place.get("editorialSummary", {}).get("text"),
                website=place.get("websiteUri"),
                phone=place.get("nationalPhoneNumber"),
                google_maps_url=place.get("googleMapsUri"),
                photos=photos
            ))

        return restaurants if restaurants else _mock_restaurants(request)

    except httpx.HTTPStatusError as e:
        logger.error(f"[RESTAURANT] HTTP {e.response.status_code}: {e.response.text}")
        return _mock_restaurants(request)
    except Exception as e:
        logger.error(f"[RESTAURANT] {type(e).__name__}: {e}")
        return _mock_restaurants(request)


# --- Fallback mock data ──────────────────────────────────────────────
def _mock_restaurants(request: RestaurantSearchRequest) -> List[Restaurant]:
    return [
        Restaurant(
            id="mock-r-1",
            name="The Golden Spoon",
            cuisine="Thai",
            rating=4.5,
            user_rating_count=120,
            price_range="$$",
            location={
                "address": f"123 Food Street, {request.destination}",
                "city": request.destination
            },
            opening_hours="Mon-Sun 11:00-23:00",
            description="Authentic local cuisine in a cozy setting.",
            website="https://example.com",
            google_maps_url="https://maps.google.com",
            photos=["https://images.unsplash.com/photo-1552566626-52f8b828add9"]
        )
    ]