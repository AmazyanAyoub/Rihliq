from pydantic import BaseModel, Field
from typing import Optional, List, Dict


# ─── Common / Shared ──────────────────────────────────────────────────────────

class Location(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


# ─── Trip ─────────────────────────────────────────────────────────────────────

class TripParseRequest(BaseModel):
    query: str = Field(..., description="Natural language trip description")
    current_state: Optional["TripState"] = None


class TripDetails(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_date: Optional[str] = None       # YYYY-MM-DD
    return_date: Optional[str] = None          # YYYY-MM-DD
    num_travelers: int = 1
    travel_class: str = "ECONOMY"              # "ECONOMY" | "PREMIUM_ECONOMY" | "BUSINESS" | "FIRST"
    preferences: List[str] = []
    budget: Optional[str] = None               # "budget" | "mid-range" | "luxury"
    trip_type: Optional[str] = None            # "leisure" | "business" | "adventure" | "romantic"


class TripState(BaseModel):
    """Tracks what we know and what we still need to ask the user."""
    details: TripDetails
    missing_fields: List[str] = []
    is_ready: bool = False
    next_question: Optional[str] = None

    @property
    def required_fields_met(self) -> bool:
        # Minimum required to call the search APIs
        required = ["origin", "destination", "departure_date"]
        missing = [f for f in required if not getattr(self.details, f)]
        return len(missing) == 0


# ─── Final Plan ───────────────────────────────────────────────────────────────

class TripPlan(BaseModel):
    """The final 'Product' returned after all APIs are called."""
    details: TripDetails
    flights: List["Flight"] = []
    hotels: List["Hotel"] = []
    restaurants: List["Restaurant"] = []
    summary: Optional[str] = None              # AI-generated itinerary summary
    total_estimated_cost: Optional[float] = None


# ─── Flights ──────────────────────────────────────────────────────────────────

class FlightBaggage(BaseModel):
    type: str                               # "checked" | "carry_on"
    quantity: int


class FlightAmenities(BaseModel):
    wifi: Optional[bool] = None
    power: Optional[bool] = None
    entertainment: Optional[bool] = None
    food: Optional[bool] = None


class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    num_travelers: int = 1
    travel_class: str = "ECONOMY"           # "ECONOMY" | "PREMIUM_ECONOMY" | "BUSINESS" | "FIRST"


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
    fare_brand: Optional[str] = None        # e.g., "Basic Economy"
    amenities: Optional[FlightAmenities] = None


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
    rating: Optional[int] = None            # stars 1-5
    review_score: Optional[float] = None    # score 1-10
    review_count: Optional[int] = None
    review_word: Optional[str] = None       # e.g., "Excellent"
    location: Location
    photos: List[str] = []
    amenities: List[str] = []
    cheapest_price: Optional[float] = None
    currency: str = "USD"
    check_in_date: Optional[str] = None
    check_out_date: Optional[str] = None
    is_free_cancellable: Optional[bool] = None
    distance_from_center: Optional[str] = None
    checkin_times: Optional[Dict[str, str]] = None  # {"from": "14:00", "until": "23:00"}


# ─── Restaurants ──────────────────────────────────────────────────────────────

class RestaurantSearchRequest(BaseModel):
    query: str
    destination: str
    limit: int = 10


class Restaurant(BaseModel):
    id: str
    name: str
    cuisine: Optional[str] = None
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    price_range: Optional[str] = None       # "$" | "$$" | "$$$" | "$$$$"
    location: Location
    opening_hours: Optional[str] = None     # "Open now" or summarized string
    description: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    google_maps_url: Optional[str] = None
    photos: List[str] = []


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str                               # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    trip_context: Optional[TripDetails] = None
    history: List[ChatMessage] = []


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    message: str
