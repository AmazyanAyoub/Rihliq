
from typing import Optional

from models.schemas import AgentState
from models.schemas import AgentState
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

def _last_user_text(state: AgentState) -> str:
    for m in reversed(state.messages):
        if isinstance(m, HumanMessage):
            return m.content
    return ""

def _last_ai_text(state: AgentState) -> str:
    for m in reversed(state.messages):
        if isinstance(m, AIMessage):
            return m.content
    return ""

def _merge(old: BaseModel, new: BaseModel) -> BaseModel:
    """Keep old values when new ones are empty."""
    merged = old.model_dump()
    for k, v in new.model_dump().items():
        if v not in (None, "", []):
            merged[k] = v
    return type(old)(**merged)


# def resolve_pick(pick: str, items: list) -> Optional[str]:
#     """Match user input to an item id. Tries number, exact id, then name substring."""
#     if not pick or not items:
#         return None
#     pick = pick.strip().lower()

#     # Try: "2" → items[1].id
#     if pick.isdigit():
#         idx = int(pick) - 1
#         if 0 <= idx < len(items):
#             return items[idx].id

#     # Try: exact id match
#     for item in items:
#         if item.id.lower() == pick:
#             return item.id

#     # Try: name substring match
#     for item in items:
#         name = getattr(item, "name", None) or getattr(item, "airline", "")
#         if pick in name.lower():
#             return item.id

#     return None


def _chat_brief(state: AgentState) -> str:
    """Build a compact internal brief — focuses on ONE active phase at a time."""
    s = state.slots
    sel = state.selections
    lines = []

    # Intent detection
    intents = []
    if s.wants_flights: intents.append("flights")
    if s.wants_hotels: intents.append("hotels")
    if not intents:
        lines.append("USER WANTS: unknown — ask openly what they need (flights, a hotel, or both).")
        return "\n".join(lines)
    lines.append(f"USER WANTS: {', '.join(intents)}")

    # Known info
    known = []
    if s.origin and s.destination:
        known.append(f"{s.origin} → {s.destination}")
    elif s.destination:
        known.append(f"destination: {s.destination}")
    elif s.origin:
        known.append(f"origin: {s.origin}")
    if s.departure_date: known.append(f"depart {s.departure_date}")
    if s.num_nights: known.append(f"{s.num_nights} nights")
    if s.num_travelers and s.num_travelers > 1: known.append(f"{s.num_travelers} travelers")
    if known: lines.append("KNOWN: " + ", ".join(known))

    # Pick ONE active phase (priority: flights → hotels)
    active = None
    if s.wants_flights and not sel.selected_flight_id:
        active = "flights"
    elif s.wants_hotels and not sel.selected_hotel_id:
        active = "hotels"

    # ── FLIGHTS
    if active == "flights":
        missing = []
        if not s.origin: missing.append("origin city")
        if not s.destination: missing.append("destination city")
        if not s.departure_date: missing.append("departure date")
        if not s.num_travelers: missing.append("how many people are traveling")
        if missing:
            lines.append(f"FLIGHTS — STILL NEED: {missing[0]}")
        elif not state.flight_confirmed and not state.flights:
            lines.append("FLIGHTS — READY TO CONFIRM: summarize the flight trip (including travelers) in one sentence and ask 'is that correct?'")
        elif state.flights and not sel.selected_flight_id:
            top = state.flights[:3]
            fl = []
            for i, f in enumerate(top, 1):
                stops = "direct" if f.stops == 0 else f"{f.stops} stop(s)"
                dep = f.departure_time.replace("T", " ")[:16]
                fl.append(f"  {i}. {f.airline} {f.flight_number} | {dep} | {f.duration} | {stops} | {f.price:.0f} {f.currency}")
            lines.append(f"FLIGHTS FOUND ({len(state.flights)} total, top 3):\n" + "\n".join(fl) + "\n→ Present these and ask which one they'd like.")

    # ── HOTELS
    elif active == "hotels":
        if not s.destination:
            lines.append("HOTELS — STILL NEED: which city to find a hotel in")
        elif not s.departure_date:
            lines.append("HOTELS — STILL NEED: check-in date")
        elif not s.num_nights:
            lines.append("HOTELS — STILL NEED: how many nights they'll stay")
        elif not state.hotels_confirmed and not state.hotels:
            lines.append(f"HOTELS — READY TO CONFIRM: ask 'shall I find hotels in {s.destination} for {s.num_nights} nights starting {s.departure_date}?'")
        elif state.hotels and not sel.selected_hotel_id:
            top = state.hotels[:3]
            hl = []
            for i, h in enumerate(top, 1):
                price = f"{h.cheapest_price:.0f} {h.currency}" if h.cheapest_price else "N/A"
                rating = f"{h.rating}★" if h.rating else "—"
                score = f"{h.review_score}/10" if h.review_score else ""
                hl.append(f"  {i}. {h.name} ({rating} {score}) | from {price}")
            lines.append(f"HOTELS FOUND ({len(state.hotels)} total, top 3):\n" + "\n".join(hl) + "\n→ Present these warmly and ask which they'd like.")

    # ── Acknowledge completed phases when moving between them
    completed = []
    if sel.selected_flight_id:
        f = next((x for x in state.flights if x.id == sel.selected_flight_id), None)
        if f: completed.append(f"flight ({f.airline} {f.flight_number}, {f.price:.0f} {f.currency})")
    if sel.selected_hotel_id:
        h = next((x for x in state.hotels if x.id == sel.selected_hotel_id), None)
        if h: completed.append(f"hotel ({h.name})")
    if completed and active:
        lines.append(f"ALREADY DONE: {', '.join(completed)}. Briefly acknowledge then focus on the active phase above.")

    # All done
    if not active:
        lines.append("ALL DONE: warmly wrap up and offer any further help.")

    return "\n".join(lines)