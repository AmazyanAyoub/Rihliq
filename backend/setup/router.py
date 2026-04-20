from models.schemas import AgentState


def router(state: AgentState) -> str:
    s = state.slots
    sel = state.selections

    if not s.wants_flights and not s.wants_hotels:
        return "chat"

    # FLIGHTS
    if s.wants_flights and not sel.selected_flight_id:
        if not s.origin or not s.destination or not s.departure_date or not s.num_travelers:
            return "chat"
        if not state.flight_confirmed:
            return "chat"
        if not state.flights:
            return "flight_search"
        return "chat"

    # HOTELS
    if s.wants_hotels and not sel.selected_hotel_id:
        if not s.destination or not s.departure_date:
            return "chat"
        if not s.num_nights:
            return "chat"
        if not state.hotels_confirmed:
            return "chat"
        if not state.hotels:
            return "hotel_search"
        return "chat"

    return "chat"