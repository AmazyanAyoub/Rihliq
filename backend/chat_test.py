import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.travel_assistant import travel_assistant


import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

async def chat_loop():
    print("====================================================")
    print("   RIHLIQ - LANGGRAPH AGENT TEST SESSION            ")
    print("====================================================")
    print("Type 'exit' to quit. Type 'reset' to start a new trip.\n")
    print("RihlIQ: Hi there! ✈️  Tell me about your trip —")
    print("        e.g. 'I want to fly from Casablanca to Paris on Dec 20'\n")

    thread_id = "test-thread-1"

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            print("RihlIQ: Safe travels! 👋")
            break
        if user_input.lower() == "reset":
            # New thread_id = fresh conversation (MemorySaver keys off thread_id)
            import uuid
            thread_id = f"test-thread-{uuid.uuid4().hex[:6]}"
            print(f"[Reset — new thread: {thread_id}]\n")
            continue

        print("\n[LangGraph is processing...]")

        try:
            state = await travel_assistant.process_message(user_input, thread_id=thread_id)

            # Main reply
            print(f"\nRihlIQ: {state.next_question}\n")

            # Debug panel
            # print("--- DEBUG STATE ---")
            # # print(f"Phase: {state.current_phase}")
            # print(f"Slots: {state.slots.model_dump(exclude_none=True)}")
            # print(f"Selections: {state.selections.model_dump(exclude_none=True)}")
            # print(f"user_wants_next_phase: {state.user_wants_next_phase}")
            # In the debug panel, replace the flight prints with this:
            # --- Replace the entire "if state.flights / hotels / restaurants" block with this ---

            # phase = state.current_phase

            # # Flights — show only while still in flights phase AND no selection yet
            # if phase == "flights" and state.flights and not state.selections.selected_flight_id:
            #     print(f"\n✈️  TOP {min(5, len(state.flights))} FLIGHTS (of {len(state.flights)}):\n")
            #     for i, f in enumerate(state.flights[:5], start=1):
            #         stops = "direct" if f.stops == 0 else f"{f.stops} stop{'s' if f.stops > 1 else ''}"
            #         dep = f.departure_time.replace("T", " ")[:16]
            #         arr = f.arrival_time.replace("T", " ")[:16]
            #         print(f"  {i}. {f.airline} {f.flight_number}")
            #         print(f"     {f.origin} → {f.destination}  |  {dep} → {arr}  ({f.duration})  |  {stops}")
            #         print(f"     💰 {f.price:.0f} {f.currency}  |  ID: {f.id}\n")

            # # Hotels — show only in hotels phase AND no selection yet
            # elif phase == "hotels" and state.hotels and not state.selections.selected_hotel_id:
            #     print(f"\n🏨 TOP {min(5, len(state.hotels))} HOTELS (of {len(state.hotels)}):\n")
            #     for i, h in enumerate(state.hotels[:5], start=1):
            #         price = f"{h.cheapest_price:.0f} {h.currency}" if h.cheapest_price else "N/A"
            #         rating = f"{h.rating}★" if h.rating else "—"
            #         score = f"{h.review_score}/10" if h.review_score else ""
            #         print(f"  {i}. {h.name}  ({rating} {score})")
            #         print(f"     💰 from {price}  |  ID: {h.id}\n")

            # # Restaurants — show only in restaurants phase
            # elif phase == "restaurants" and state.restaurants:
            #     print(f"\n🍽️  TOP {min(5, len(state.restaurants))} RESTAURANTS (of {len(state.restaurants)}):\n")
            #     for i, r in enumerate(state.restaurants[:5], start=1):
            #         rating = f"{r.rating}★" if r.rating else "—"
            #         cuisine = r.cuisine or "—"
            #         print(f"  {i}. {r.name}  ({rating}, {cuisine})")
            #         print(f"     ID: {r.id}\n")

            # picked = []
            # if state.selections.selected_flight_id:
            #     f = next((x for x in state.flights if x.id == state.selections.selected_flight_id), None)
            #     if f:
            #         picked.append(f"✈️  {f.airline} {f.flight_number}  ({f.price:.0f} {f.currency})")
            # if state.selections.selected_hotel_id:
            #     h = next((x for x in state.hotels if x.id == state.selections.selected_hotel_id), None)
            #     if h:
            #         picked.append(f"🏨 {h.name}")
            # if picked:
            #     print("\n📌 LOCKED IN:")
            #     for p in picked:
            #         print(f"   {p}")
            # print("-------------------\n")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()


if __name__ == "__main__":
    asyncio.run(chat_loop())