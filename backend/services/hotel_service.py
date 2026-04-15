import logging
from typing import List, Tuple

import httpx

from config import settings
from models.schemas import Hotel, HotelSearchRequest

logger = logging.getLogger(__name__)

# ── Booking.com API (by tipsters) on RapidAPI ──────────────────────
RAPIDAPI_HOST = "booking-com.p.rapidapi.com"
RAPIDAPI_BASE = f"https://{RAPIDAPI_HOST}"


def _get_headers() -> dict:
    return {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key":  settings.rapidapi_key,
    }


async def _get_destination(
    client: httpx.AsyncClient, destination: str
) -> Tuple[str, str] | None:
    """
    Step 1 — resolve a city/place name to a Booking.com dest_id + dest_type.
    Returns (dest_id, dest_type) or None.
    """
    res = await client.get(
        f"{RAPIDAPI_BASE}/v1/hotels/locations",
        headers=_get_headers(),
        params={
            "name":   destination,
            "locale": "en-gb",
        },
    )
    res.raise_for_status()
    data = res.json()

    logger.info(f"[HOTEL] Destination response: {data}")

    if not data:
        return None

    # Prefer a "city" type result, fall back to the first match
    for item in data:
        if item.get("dest_type") == "city":
            return item["dest_id"], item["dest_type"]

    first = data[0]
    return first.get("dest_id"), first.get("dest_type", "city")


async def search_hotels(request: HotelSearchRequest) -> List[Hotel]:
    if not settings.rapidapi_key:
        logger.warning("RapidAPI key not set — returning mock hotels")
        return _mock_hotels(request)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1 — resolve destination
            dest = await _get_destination(client, request.destination)
            if not dest:
                logger.warning(f"Could not resolve destination: {request.destination}")
                return _mock_hotels(request)

            dest_id, dest_type = dest

            # Step 2 — search hotels
            res = await client.get(
                f"{RAPIDAPI_BASE}/v1/hotels/search",
                headers=_get_headers(),
                params={
                    "dest_id":            dest_id,
                    "dest_type":          dest_type,
                    "checkin_date":       request.check_in,
                    "checkout_date":      request.check_out,
                    "adults_number":      request.num_guests,
                    "room_number":        request.num_rooms,
                    "order_by":           "popularity",
                    "filter_by_currency": "USD",
                    "locale":             "en-gb",
                    "units":              "metric",
                    "page_number":        "0",
                    "include_adjacency":  "true",
                },
            )
            res.raise_for_status()
            raw = res.json()
            logger.info(f"[HOTEL] Raw response keys: {list(raw.keys())}")

            # The Booking.com API nests results under "result"
            properties = raw.get("result", [])
            logger.info(f"[HOTEL] Properties found: {len(properties)}")

        hotels: List[Hotel] = []
        for prop in properties[:20]:
            # ── Price ──
            price = prop.get("min_total_price") or prop.get("composite_price_breakdown", {}).get(
                "gross_amount_per_night", {}
            ).get("value")

            # ── Star rating ──
            star_rating = prop.get("class")  # 1-5

            # ── Reviews ──
            review_score = prop.get("review_score")          # e.g. 8.5
            review_count = prop.get("review_nr")             # e.g. 1234
            review_word  = prop.get("review_score_word", "") # e.g. "Excellent"

            # ── Location ──
            latitude  = prop.get("latitude")
            longitude = prop.get("longitude")

            # ── Photo ──
            photo_url = prop.get("main_photo_url") or prop.get("max_photo_url")
            # Booking often gives a "square60" thumb; swap for a larger size
            if photo_url:
                photo_url = photo_url.replace("square60", "square600")
            photos = [photo_url] if photo_url else []

            hotels.append(Hotel(
                id=str(prop.get("hotel_id", "")),
                name=prop.get("hotel_name") or prop.get("hotel_name_trans", "Unknown Hotel"),
                rating=int(star_rating) if star_rating else None,
                review_score=float(review_score) if review_score else None,
                review_count=int(review_count) if review_count else None,
                address=prop.get("address") or prop.get("address_trans"),
                city=prop.get("city") or prop.get("city_trans") or request.destination,
                latitude=float(latitude) if latitude else None,
                longitude=float(longitude) if longitude else None,
                photos=photos,
                amenities=[],                         # details endpoint needed for full amenities
                cheapest_price=float(price) if price else None,
                currency=prop.get("currency_code") or prop.get("currencycode") or "USD",
                check_in_date=request.check_in,
                check_out_date=request.check_out,
            ))

        return hotels if hotels else _mock_hotels(request)

    except httpx.HTTPStatusError as e:
        logger.error(f"[HOTEL ERROR] HTTP {e.response.status_code}: {e.response.text}")
        return _mock_hotels(request)
    except Exception as e:
        logger.error(f"[HOTEL ERROR] {type(e).__name__}: {e}")
        return _mock_hotels(request)


# ── Fallback mock data ──────────────────────────────────────────────
def _mock_hotels(request: HotelSearchRequest) -> List[Hotel]:
    return [
        Hotel(
            id="mock-hotel-1",
            name="Grand Palace Hotel",
            rating=5,
            review_score=9.2,
            review_count=1840,
            address=f"123 Main Street, {request.destination}",
            city=request.destination,
            latitude=None,
            longitude=None,
            photos=[],
            amenities=["WiFi", "Pool", "Gym", "Spa", "Restaurant", "Room Service"],
            cheapest_price=189.00,
            currency="USD",
            check_in_date=request.check_in,
            check_out_date=request.check_out,
        ),
        Hotel(
            id="mock-hotel-2",
            name="Comfort Suites",
            rating=3,
            review_score=7.8,
            review_count=632,
            address=f"456 Travel Road, {request.destination}",
            city=request.destination,
            latitude=None,
            longitude=None,
            photos=[],
            amenities=["WiFi", "Breakfast Included", "Parking"],
            cheapest_price=89.00,
            currency="USD",
            check_in_date=request.check_in,
            check_out_date=request.check_out,
        ),
        Hotel(
            id="mock-hotel-3",
            name="Boutique Stay",
            rating=4,
            review_score=8.5,
            review_count=410,
            address=f"789 Culture Lane, {request.destination}",
            city=request.destination,
            latitude=None,
            longitude=None,
            photos=[],
            amenities=["WiFi", "Bar", "Concierge", "Room Service", "Airport Shuttle"],
            cheapest_price=145.00,
            currency="USD",
            check_in_date=request.check_in,
            check_out_date=request.check_out,
        ),
    ]