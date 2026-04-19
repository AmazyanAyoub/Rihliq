from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union, Literal, Annotated
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

class Restaurant(BaseModel):
    id: str
    name: str
    cuisine: Optional[str] = None
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    price_range: Optional[str] = None
    location: Location
    opening_hours: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    google_maps_url: Optional[str] = None
    photos: List[str] = []


# ─── Trip Slots & Selections ──────────────────────────────────────────────────

class TripDetails(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    num_travelers: Optional[int] = None
    travel_class: str = "ECONOMY"
    preferences: List[str] = []
    budget: Optional[str] = None
    trip_type: Optional[str] = None

class TripSlots(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    num_nights: Optional[int] = None
    num_travelers: Optional[int] = None
    travel_class: str = "ECONOMY"
    budget: Optional[str] = None
    trip_type: Optional[str] = None
    preferences: List[str] = []
    wants_flights: bool = False
    wants_hotels: bool = False
    wants_restaurants: bool = False
    cuisine_preference: Optional[str] = None

class TripSelections(BaseModel):
    selected_flight_id: Optional[str] = None
    selected_hotel_id: Optional[str] = None
    # selected_restaurant_ids: List[str] = []


# ─── LangGraph State ──────────────────────────────────────────────────────────

class AgentState(BaseModel):
    """The global state carried through the LangGraph."""
    slots: TripSlots = Field(default_factory=TripSlots)
    selections: TripSelections = Field(default_factory=TripSelections)
    
    # Typed Results
    flights: List[Flight] = []
    hotels: List[Hotel] = []
    restaurants: List[Restaurant] = []
    
    # Flow Control
    current_phase: Literal["flights", "hotels", "restaurants", "summary", "done"] = "flights"
    user_wants_next_phase: Optional[bool] = None
    
    # Message History (Annotated for automatic accumulation)
    messages: Annotated[list, add_messages] = []
    
    next_question: Optional[str] = None
    is_complete: bool = False
    trip_confirmed: bool = False

    hotels_confirmed: bool = False
    restaurants_confirmed: bool = False


# ─── Requests ─────────────────────────────────────────────────────────────────

class TripParseRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    current_state: Optional[AgentState] = None

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    num_travelers: Optional[int] = None
    travel_class: str = "ECONOMY"

class HotelSearchRequest(BaseModel):
    destination: str
    check_in: str
    check_out: str
    num_guests: Optional[int] = None
    num_rooms: int = 1

class RestaurantSearchRequest(BaseModel):
    query: str
    destination: str
    limit: int = 10


