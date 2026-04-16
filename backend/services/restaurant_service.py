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
            # ── ID ──
            place_id = place.get("id", "")

            # ── Name (new API nests it under displayName.text) ──
            display_name = place.get("displayName", {})
            name = display_name.get("text", "Unknown") if isinstance(display_name, dict) else str(display_name)

            # ── Cuisine / type ──
            cuisine = None
            primary_type_display = place.get("primaryTypeDisplayName", {})
            if isinstance(primary_type_display, dict):
                cuisine = primary_type_display.get("text")
            if not cuisine:
                cuisine = place.get("primaryType", "Restaurant")

            # ── Rating (Google uses 1.0 - 5.0 scale) ──
            rating = float(place.get("rating") or 0.0)

            # ── Review count ──
            user_rating_count = place.get("userRatingCount")

            # ── Price level ──
            price_level = place.get("priceLevel")
            price_range = PRICE_MAP.get(price_level, "$$")

            # ── Address ──
            address = place.get("formattedAddress", "")

            # ── City (extract from address) ──
            address_parts = [p.strip() for p in address.split(",")]
            city = address_parts[-2] if len(address_parts) >= 2 else request.destination

            # ── Coordinates ──
            location  = place.get("location", {})
            latitude  = location.get("latitude")
            longitude = location.get("longitude")

            # ── Opening hours ──
            opening_hours = None
            current_hours = place.get("currentOpeningHours") or place.get("regularOpeningHours")
            if current_hours:
                # weekdayDescriptions is a list like:
                # ["Monday: 10:00 AM – 10:00 PM", "Tuesday: 10:00 AM – 10:00 PM", ...]
                weekday_desc = current_hours.get("weekdayDescriptions", [])
                if weekday_desc:
                    opening_hours = " | ".join(weekday_desc)
                elif current_hours.get("openNow") is not None:
                    opening_hours = "Open now" if current_hours["openNow"] else "Closed now"

            # ── Website ──
            website = place.get("websiteUri")

            # ── Phone ──
            phone = place.get("nationalPhoneNumber")

            # ── Photo (first one if available) ──
            photos_list = place.get("photos", [])
            photo_ref = None
            if photos_list:
                # New API returns photo resource names like:
                # "places/PLACE_ID/photos/PHOTO_REF"
                photo_name = photos_list[0].get("name", "")
                if photo_name:
                    photo_ref = (
                        f"https://places.googleapis.com/v1/{photo_name}/media"
                        f"?maxHeightPx=400&key={settings.google_maps_api_key}"
                    )

            restaurants.append(Restaurant(
                id=place_id,
                name=name,
                cuisine=cuisine,
                rating=rating,
                price_range=price_range,
                address=address,
                opening_hours=opening_hours,
                description=None,
                city=city,
                # If your Restaurant schema supports these extra fields, uncomment:
                # latitude=latitude,
                # longitude=longitude,
                # phone=phone,
                # website=website,
                # photo_url=photo_ref,
                # user_rating_count=user_rating_count,
            ))

        return restaurants if restaurants else _mock_restaurants(request)

    except httpx.HTTPStatusError as e:
        logger.error(f"[RESTAURANT] HTTP {e.response.status_code}: {e.response.text}")
        return _mock_restaurants(request)
    except Exception as e:
        logger.error(f"[RESTAURANT] {type(e).__name__}: {e}")
        return _mock_restaurants(request)


# ── Fallback mock data ──────────────────────────────────────────────
def _mock_restaurants(request: RestaurantSearchRequest) -> List[Restaurant]:
    return [
        Restaurant(
            id="mock-r-1",
            name="The Golden Spoon",
            cuisine="Thai",
            rating=4.5,
            price_range="$$",
            address=f"123 Food Street, {request.destination}",
            opening_hours="Mon-Sun 11:00-23:00",
            description="Authentic local cuisine in a cozy setting.",
            city=request.destination,
        ),
        Restaurant(
            id="mock-r-2",
            name="Sakura Garden",
            cuisine="Japanese",
            rating=4.3,
            price_range="$$$",
            address=f"456 Dining Ave, {request.destination}",
            opening_hours="Mon-Sun 12:00-22:00",
            description="Fresh sushi and traditional Japanese dishes.",
            city=request.destination,
        ),
        Restaurant(
            id="mock-r-3",
            name="La Piazza",
            cuisine="Italian",
            rating=4.2,
            price_range="$$",
            address=f"789 Taste Blvd, {request.destination}",
            opening_hours="Tue-Sun 13:00-23:00",
            description="Wood-fired pizzas and homemade pasta.",
            city=request.destination,
        ),
    ]