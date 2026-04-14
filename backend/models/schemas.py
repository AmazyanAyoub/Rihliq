from pydantic import BaseModel, Field
from typing import Optional, List


# ─── Trip ─────────────────────────────────────────────────────────────────────

class TripParseRequest(BaseModel):
    query: str = Field(..., description="Natural language trip description")


class TripDetails(BaseModel):
    origin: str
    destination: str
    departure_date: str                     # YYYY-MM-DD
    return_date: Optional[str] = None       # YYYY-MM-DD
    num_travelers: int = 1
    preferences: Optional[List[str]] = []
    budget: Optional[str] = None            # "budget" | "mid-range" | "luxury"
    trip_type: Optional[str] = None         # "leisure" | "business" | "adventure" | "romantic"


# ─── Flights ──────────────────────────────────────────────────────────────────

class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    num_travelers: int = 1
    travel_class: str = "ECONOMY"


class Flight(BaseModel):
    id: str
    airline: str
    airline_code: str
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


# ─── Hotels ───────────────────────────────────────────────────────────────────

class HotelSearchRequest(BaseModel):
    destination: str
    check_in: str
    check_out: str
    num_guests: int = 1
    num_rooms: int = 1


class Hotel(BaseModel):
    id: str
    name: str
    address: str
    rating: Optional[float] = None
    stars: Optional[int] = None
    price_per_night: Optional[float] = None
    currency: str = "USD"
    amenities: List[str] = []
    image_url: Optional[str] = None
    description: Optional[str] = None


# ─── Restaurants ──────────────────────────────────────────────────────────────

class RestaurantSearchRequest(BaseModel):
    query: str
    destination: str
    limit: int = 10


class Restaurant(BaseModel):
    id: str
    name: str
    cuisine: str
    rating: float
    price_range: str        # "$" | "$$" | "$$$" | "$$$$"
    address: str
    opening_hours: Optional[str] = None
    description: Optional[str] = None
    city: str


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str       # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    trip_context: Optional[TripDetails] = None
    history: List[ChatMessage] = []


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    message: str
