import asyncio
import logging
from typing import List

from duffel_api import Duffel # Changed import

from config import settings
from models.schemas import Flight, FlightSearchRequest

logger = logging.getLogger(__name__)


def _get_client() -> Duffel:
    return Duffel(access_token=settings.duffel_access_token) # Uses single token

def _parse_duration(iso: str) -> str:
    """Convert PT6H30M → 6h 30m"""
    iso = iso.replace("PT", "")
    result = ""
    if "H" in iso:
        parts = iso.split("H")
        result += f"{parts[0]}h "
        iso = parts[1]
    if "M" in iso:
        result += f"{iso.replace('M', '')}m"
    return result.strip()


def _search_sync(request: FlightSearchRequest) -> List[Flight]:
    duffel = _get_client()

    # 1. Build the slices (legs of the journey)
    slices = [
        {
            "origin": request.origin.upper(),
            "destination": request.destination.upper(),
            "departure_date": request.departure_date,
        }
    ]
    
    if request.return_date:
        slices.append({
            "origin": request.destination.upper(),
            "destination": request.origin.upper(),
            "departure_date": request.return_date,
        })

    # 2. Build passenger array
    passengers = [{"type": "adult"} for _ in range(request.num_travelers)]
    
    # Map travel class (Duffel expects lower case: economy, premium_economy, business, first)
    cabin = request.travel_class.lower() if request.travel_class else "economy"

    # 3. Make the API Call
    offer_request = duffel.offer_requests.create(
        return_offers=True,
        slices=slices,
        passengers=passengers,
        cabin_class=cabin,
    )

    flights = []
    # 4. Parse the clean JSON response
    for offer in offer_request.offers[:20]: # Limit to 20 results like before
        slice_out = offer.slices[0]
        segments = slice_out.segments
        first = segments[0]
        last = segments[-1]

        flights.append(Flight(
            id=offer.id,
            airline=first.operating_carrier.name,
            airline_code=first.operating_carrier.iata_code,
            flight_number=f"{first.operating_carrier.iata_code}{first.operating_carrier_flight_number}",
            origin=first.origin.iata_code,
            destination=last.destination.iata_code,
            departure_time=first.departing_at,
            arrival_time=last.arriving_at,
            duration=_parse_duration(slice_out.duration),
            stops=len(segments) - 1,
            price=float(offer.total_amount),
            currency=offer.total_currency,
            travel_class=request.travel_class,
        ))

    return sorted(flights, key=lambda f: f.price)


async def search_flights(request: FlightSearchRequest) -> List[Flight]:
    if not settings.duffel_access_token: # Update validation check
        logger.warning("Duffel credentials not set — returning mock flights")
        return _mock_flights(request)

    try:
        # Duffel SDK is also synchronous — run in thread pool
        return await asyncio.to_thread(_search_sync, request)
    except Exception as e: # Catch all exceptions for the mock fallback
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
