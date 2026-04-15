import logging
from typing import List

import httpx

from config import settings
from models.schemas import Flight, FlightSearchRequest

logger = logging.getLogger(__name__)

DUFFEL_BASE_URL = "https://api.duffel.com"


def _get_headers() -> dict:
    return {
        "Authorization":  f"Bearer {settings.duffel_access_token}",
        "Duffel-Version": "v2",
        "Content-Type":   "application/json",
        "Accept":         "application/json",
    }


def _parse_duration(iso: str) -> str:
    """Convert PT6H30M → 6h 30m"""
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
        logger.warning("Duffel credentials not set — returning mock flights")
        return _mock_flights(request)

    try:
        # Build slices
        slices = [
            {
                "origin":         request.origin.upper(),
                "destination":    request.destination.upper(),
                "departure_date": request.departure_date,
            }
        ]
        if request.return_date:
            slices.append({
                "origin":         request.destination.upper(),
                "destination":    request.origin.upper(),
                "departure_date": request.return_date,
            })

        # Build passengers
        passengers = [{"type": "adult"} for _ in range(request.num_travelers)]

        cabin = request.travel_class.lower() if request.travel_class else "economy"

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1 — create offer request
            offer_req_res = await client.post(
                f"{DUFFEL_BASE_URL}/air/offer_requests",
                headers=_get_headers(),
                json={
                    "data": {
                        "slices":      slices,
                        "passengers":  passengers,
                        "cabin_class": cabin,
                    }
                },
            )
            offer_req_res.raise_for_status()
            offer_request_id = offer_req_res.json()["data"]["id"]

            # Step 2 — list offers
            offers_res = await client.get(
                f"{DUFFEL_BASE_URL}/air/offers",
                headers=_get_headers(),
                params={
                    "offer_request_id": offer_request_id,
                    "limit":            20,
                    "sort":             "total_amount",
                },
            )
            offers_res.raise_for_status()
            offers = offers_res.json()["data"]

        flights = []
        for offer in offers:
            slice_out = offer["slices"][0]
            segments  = slice_out["segments"]
            first     = segments[0]
            last      = segments[-1]

            flights.append(Flight(
                id=offer["id"],
                airline=first["operating_carrier"]["name"],
                airline_code=first["operating_carrier"]["iata_code"],
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
            ))

        return flights

    except httpx.HTTPStatusError as e:
        logger.error(f"Duffel API error {e.response.status_code}: {e.response.text}")
        return _mock_flights(request)
    except Exception as e:
        logger.error(f"Flight search failed: {e}")
        return _mock_flights(request)


def _mock_flights(request: FlightSearchRequest) -> List[Flight]:
    return [
        Flight(
            id="mock-1",
            airline="American Airlines",
            airline_code="AA",
            flight_number="AA100",
            origin=request.origin.upper(),
            destination=request.destination.upper(),
            departure_time=f"{request.departure_date}T08:00:00",
            arrival_time=f"{request.departure_date}T14:30:00",
            duration="6h 30m",
            stops=0,
            price=450.00,
            currency="USD",
            travel_class=request.travel_class,
        ),
        Flight(
            id="mock-2",
            airline="Delta Air Lines",
            airline_code="DL",
            flight_number="DL205",
            origin=request.origin.upper(),
            destination=request.destination.upper(),
            departure_time=f"{request.departure_date}T11:00:00",
            arrival_time=f"{request.departure_date}T19:45:00",
            duration="8h 45m",
            stops=1,
            price=320.00,
            currency="USD",
            travel_class=request.travel_class,
        ),
        Flight(
            id="mock-3",
            airline="United Airlines",
            airline_code="UA",
            flight_number="UA450",
            origin=request.origin.upper(),
            destination=request.destination.upper(),
            departure_time=f"{request.departure_date}T15:00:00",
            arrival_time=f"{request.departure_date}T22:15:00",
            duration="7h 15m",
            stops=0,
            price=520.00,
            currency="USD",
            travel_class=request.travel_class,
        ),
    ]
