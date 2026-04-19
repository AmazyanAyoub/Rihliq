import logging
import re
from typing import List, Optional

import httpx

from config import settings
from models.schemas import Flight, FlightSearchRequest

logger = logging.getLogger(__name__)

DUFFEL_BASE_URL = "https://api.duffel.com"
IATA_RE = re.compile(r"^[A-Z]{3}$")

# In-process cache: {"casablanca": "CMN"}
_iata_cache: dict[str, str] = {}


class FlightSearchError(Exception):
    """Raised when flight search cannot complete."""


def _get_headers() -> dict:
    return {
        "Authorization":  f"Bearer {settings.duffel_access_token}",
        "Duffel-Version": "v2",
        "Content-Type":   "application/json",
        "Accept":         "application/json",
    }


async def _resolve_to_iata(client: httpx.AsyncClient, name: str) -> str:
    """Resolve any city/airport name to IATA via Duffel Places. Raises on failure."""
    if not name:
        raise FlightSearchError("Empty location")

    cleaned = name.strip()

    # Already IATA? done.
    if len(cleaned) == 3 and IATA_RE.match(cleaned.upper()):
        return cleaned.upper()

    key = cleaned.lower()
    if key in _iata_cache:
        return _iata_cache[key]

    res = await client.get(
        f"{DUFFEL_BASE_URL}/places/suggestions",
        headers=_get_headers(),
        params={"query": cleaned},
    )
    res.raise_for_status()
    places = res.json().get("data", [])

    # Prefer city codes (covers all airports in that city), fall back to airport code
    for p in places:
        code = p.get("iata_city_code") or p.get("iata_code")
        if code:
            _iata_cache[key] = code
            logger.info(f"Resolved '{name}' → {code}")
            return code

    raise FlightSearchError(f"Could not find airport for '{name}'")


def _parse_duration(iso: str) -> str:
    if not iso:
        return ""
    iso = iso.replace("PT", "")
    result = ""
    if "H" in iso:
        parts = iso.split("H")
        result += f"{parts[0]}h "
        iso = parts[1]
    if "M" in iso:
        result += f"{iso.replace('M', '')}m"
    return result.strip()


async def search_flights(request: FlightSearchRequest) -> List[Flight]:
    if not settings.duffel_access_token:
        raise FlightSearchError("Duffel access token not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        origin_iata = await _resolve_to_iata(client, request.origin)
        dest_iata   = await _resolve_to_iata(client, request.destination)

        slices = [{
            "origin":         origin_iata,
            "destination":    dest_iata,
            "departure_date": request.departure_date,
        }]
        if request.return_date:
            slices.append({
                "origin":         dest_iata,
                "destination":    origin_iata,
                "departure_date": request.return_date,
            })

        passengers = [{"type": "adult"} for _ in range(request.num_travelers)]
        cabin = (request.travel_class or "economy").lower()

        try:
            offer_req_res = await client.post(
                f"{DUFFEL_BASE_URL}/air/offer_requests",
                headers=_get_headers(),
                json={"data": {"slices": slices, "passengers": passengers, "cabin_class": cabin}},
            )
            offer_req_res.raise_for_status()
            offer_request_id = offer_req_res.json()["data"]["id"]

            offers_res = await client.get(
                f"{DUFFEL_BASE_URL}/air/offers",
                headers=_get_headers(),
                params={"offer_request_id": offer_request_id, "limit": 20, "sort": "total_amount"},
            )
            offers_res.raise_for_status()
            offers = offers_res.json()["data"]
        except httpx.HTTPStatusError as e:
            logger.error(f"Duffel API error {e.response.status_code}: {e.response.text}")
            raise FlightSearchError(f"Duffel API rejected the search: {e.response.status_code}") from e

    flights = []
    for offer in offers:
        slice_out = offer["slices"][0]
        segments  = slice_out["segments"]
        first     = segments[0]
        last      = segments[-1]

        baggage_info = []
        if "passengers" in first and first["passengers"]:
            for bag in first["passengers"][0].get("baggages", []):
                baggage_info.append({"type": bag.get("type"), "quantity": bag.get("quantity")})

        flights.append(Flight(
            id=offer["id"],
            airline=first["operating_carrier"]["name"],
            airline_code=first["operating_carrier"]["iata_code"],
            airline_logo=first["operating_carrier"].get("logo_symbol_url"),
            flight_number=f"{first['operating_carrier']['iata_code']}{first['operating_carrier_flight_number']}",
            origin=first["origin"]["iata_code"],
            destination=last["destination"]["iata_code"],
            departure_time=first["departing_at"],
            arrival_time=last["arriving_at"],
            duration=_parse_duration(slice_out["duration"]),
            stops=len(segments) - 1,
            price=float(offer["total_amount"]),
            currency=offer["total_currency"],
            travel_class=request.travel_class,
            baggage=baggage_info,
            carbon_emissions_kg=float(offer.get("total_emissions_kg", 0)) if offer.get("total_emissions_kg") else None,
            fare_brand=slice_out.get("fare_brand_name"),
        ))

    return flights