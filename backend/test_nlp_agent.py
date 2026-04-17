import asyncio
import json
from services.nlp_parser import nlp_parser
from models.schemas import TripState

async def simulate_conversation():
    print("--- Turn 1: Initial Request ---")
    user_msg_1 = "I'm thinking of a trip to Paris."
    state_1 = await nlp_parser.parse_trip(user_msg_1)
    
    print(f"User: {user_msg_1}")
    print(f"AI Question: {state_1.next_question}")
    print(f"Missing: {state_1.missing_fields}")
    print(f"Ready: {state_1.is_ready}\n")

    print("--- Turn 2: Providing Origin ---")
    user_msg_2 = "I'll be flying from London."
    state_2 = await nlp_parser.parse_trip(user_msg_2, current_state=state_1)
    
    print(f"User: {user_msg_2}")
    print(f"AI Question: {state_2.next_question}")
    print(f"Missing: {state_2.missing_fields}")
    print(f"Ready: {state_2.is_ready}\n")

    print("--- Turn 3: Providing Dates ---")
    user_msg_3 = "I want to go on June 15th, 2026."
    state_3 = await nlp_parser.parse_trip(user_msg_3, current_state=state_2)
    
    print(f"User: {user_msg_3}")
    print(f"AI Question: {state_3.next_question}")
    print(f"Details: {state_3.details.model_dump_json(indent=2)}")
    print(f"Ready: {state_3.is_ready}")

if __name__ == "__main__":
    asyncio.run(simulate_conversation())
