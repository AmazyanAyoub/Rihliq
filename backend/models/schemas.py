from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Annotated
from langgraph.graph.message import add_messages


# ─── Common / Shared ──────────────────────────────────────────────────────────

class Location(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


# ─── API Schemas ──────────────────────────────────────────────────────────────

class FlightBaggage(BaseModel):
    type: str
    quantity: int


class Flight(BaseModel):
    id: str
    airline: str
    airline_code: str
    airline_logo: Optional[str] = None
    flight_number: str
    origin: str
    destination: str
    departure_time: str
    arrival_time: str
    duration: str
    stops: int
    price: float
    currency: str = "USD"
    travel_class: str = "ECONOMY"
    baggage: List[FlightBaggage] = []
    carbon_emissions_kg: Optional[float] = None
    fare_brand: Optional[str] = None


# ─── Trip Slots & Selections ──────────────────────────────────────────────────

class TripSlots(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    num_travelers: Optional[int] = None
    travel_class: str = "ECONOMY"
    budget: Optional[str] = None
    trip_type: Optional[str] = None
    preferences: List[str] = []
    check_in: Optional[str] = None
    num_nights: Optional[int] = None
    wants_flights: bool = False
    wants_hotels: bool = False


class TripSelections(BaseModel):
    selected_flight_id: Optional[str] = None
    selected_hotel_id: Optional[str] = None

# ─── LangGraph State ──────────────────────────────────────────────────────────

class AgentState(BaseModel):
    """The global state carried through the LangGraph."""
    slots: TripSlots = Field(default_factory=TripSlots)
    selections: TripSelections = Field(default_factory=TripSelections)

    # Typed Results
    flights: List[Flight] = []
    flight_confirmed: bool = False

    # Message History (auto-accumulating)
    messages: Annotated[list, add_messages] = []

    next_question: Optional[str] = None
    is_complete: bool = False

    hotels: List[Hotel] = []
    hotels_confirmed: bool = False


class Hotel(BaseModel):
    id: str
    name: str
    rating: Optional[int] = None
    review_score: Optional[float] = None
    review_count: Optional[int] = None
    review_word: Optional[str] = None
    location: Location
    photos: List[str] = []
    amenities: List[str] = []
    cheapest_price: Optional[float] = None
    currency: str = "USD"
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    is_free_cancellable: Optional[bool] = None
    distance_from_center: Optional[str] = None
    checkin_times: Optional[Dict[str, str]] = None


class HotelSearchRequest(BaseModel):
    destination: str
    check_in: str
    check_out: str
    num_guests: Optional[int] = None
    num_rooms: int = 1

# ─── Requests ─────────────────────────────────────────────────────────────────

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    num_travelers: Optional[int] = None
    travel_class: str = "ECONOMY"


AgentState.model_rebuild()