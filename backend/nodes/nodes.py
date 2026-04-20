from setup.prompts import SYSTEM_EXTRACT, CHAT_SYSTEM, ExtractionResult
from typing import Dict, Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from models.schemas import (
    AgentState,
    FlightSearchRequest, HotelSearchRequest
)
from services.flight_service import search_flights, FlightSearchError
from services.hotel_service import search_hotels
from datetime import date, datetime, timedelta

from setup.helpers import _merge, _last_user_text, resolve_pick, _chat_brief
from setup.llm import get_llm

async def chat_node(state: AgentState) -> Dict:
    """The warm, human voice of the agent."""
    llm = get_llm(0.7)
    brief = _chat_brief(state)
    history = state.messages[-5:] if state.messages else []

    response = await llm.ainvoke([
        SystemMessage(content=CHAT_SYSTEM),
        *history,
        HumanMessage(content=f"[Internal brief — do not mention to user]\n{brief}\n\nReply to the user now."),
    ])
    return {"messages": [AIMessage(content=response.content)], "next_question": response.content}


async def extractor_node(state: AgentState) -> Dict:
    llm = get_llm(0).with_structured_output(ExtractionResult)
    user_msg = _last_user_text(state)

    result: ExtractionResult = await llm.ainvoke([
        SystemMessage(content=SYSTEM_EXTRACT),
        HumanMessage(content=f"""Today: {date.today()}
            Slots: {state.slots.model_dump_json()}
            Selections: {state.selections.model_dump_json()}
            User said: "{user_msg}" """),
        ])

    # Always flag flights as wanted in this mode
    new_slots = _merge(state.slots, result.slots)
    # new_slots.wants_flights = True   # Force flights mode for now, since that's all we have

    new_selections = _merge(state.selections, result.selections)

    # Resolve user_pick to a real ID — tries flights first, then hotels
    if result.user_pick:
        if state.flights and not new_selections.selected_flight_id:
            m = resolve_pick(result.user_pick, state.flights)
            if m: new_selections.selected_flight_id = m
        if state.hotels and not new_selections.selected_hotel_id:
            m = resolve_pick(result.user_pick, state.hotels)
            if m: new_selections.selected_hotel_id = m

    # Sanity checks — clear invalid IDs
    valid_flight_ids = {f.id for f in state.flights}
    if new_selections.selected_flight_id and valid_flight_ids and new_selections.selected_flight_id not in valid_flight_ids:
        new_selections.selected_flight_id = None
    valid_hotel_ids = {h.id for h in state.hotels}
    if new_selections.selected_hotel_id and valid_hotel_ids and new_selections.selected_hotel_id not in valid_hotel_ids:
        new_selections.selected_hotel_id = None

    update = {
        "slots": new_slots,
        "selections": new_selections,
    }
    if result.flight_confirmed is True:
        update["flight_confirmed"] = True
    if result.hotels_confirmed is True:
        update["hotels_confirmed"] = True
    return update


async def flight_search_node(state: AgentState) -> Dict:
    req = FlightSearchRequest(
        origin=state.slots.origin,
        destination=state.slots.destination,
        departure_date=state.slots.departure_date,
        return_date=state.slots.return_date,
        num_travelers=state.slots.num_travelers,
        travel_class=state.slots.travel_class,
    )
    try:
        flights = await search_flights(req)
    except FlightSearchError as e:
        msg = f"Hmm, I couldn't find flights — {e}. Could you double-check the cities and date?"
        return {"flights": [], "messages": [AIMessage(content=msg)], "next_question": msg}

    # Just return the data. chat_node will present it warmly.
    return {"flights": flights, "current_phase": "flights"}


async def hotel_search_node(state: AgentState) -> Dict:
    check_in = state.slots.departure_date
    check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
    nights = state.slots.num_nights or 3
    check_out = (check_in_dt + timedelta(days=nights)).strftime("%Y-%m-%d")

    req = HotelSearchRequest(
        destination=state.slots.destination,
        check_in=check_in,
        check_out=check_out,
        num_guests=state.slots.num_travelers or 1,
    )
    hotels = await search_hotels(req)
    return {"hotels": hotels}