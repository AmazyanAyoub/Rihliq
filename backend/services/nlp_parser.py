import json
from datetime import date
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.schemas import TripDetails, TripState


SYSTEM_PROMPT = """You are an expert AI Travel Agent for RihlIQ. Your goal is to gather all necessary information to plan a perfect trip.

MANDATORY FIELDS for a search:
1. origin (City/Airport)
2. destination (City/Airport)
3. departure_date (YYYY-MM-DD)

OPTIONAL BUT HELPFUL:
- return_date (YYYY-MM-DD)
- num_travelers (default 1)
- travel_class (ECONOMY, BUSINESS, etc.)
- budget (budget, mid-range, luxury)
- trip_type (leisure, business, adventure, romantic)

YOUR TASKS:
1. Extract any new information from the user's message.
2. Merge it with the 'Current Context' provided.
3. If MANDATORY FIELDS are missing:
   - Set "is_ready" to false.
   - List the missing fields in "missing_fields".
   - Write a friendly, conversational "next_question" to ask the user for ONE or TWO missing pieces.
4. If all MANDATORY FIELDS are present:
   - Set "is_ready" to true.
   - Set "next_question" to null.
   - Refine any other details you can.

You ONLY output valid JSON. No prose. No markdown."""

HUMAN_TEMPLATE = """Today's Date: {today}

Current Context (what we already know):
{current_context}

User's New Message: "{query}"

Output the updated state in this JSON format:
{{
  "details": {{
    "origin": "string or null",
    "destination": "string or null",
    "departure_date": "YYYY-MM-DD or null",
    "return_date": "YYYY-MM-DD or null",
    "num_travelers": integer,
    "travel_class": "string",
    "preferences": ["list of strings"],
    "budget": "string or null",
    "trip_type": "string or null"
  }},
  "missing_fields": ["list of strings"],
  "is_ready": boolean,
  "next_question": "string or null"
}}
"""


class NLPParser:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gemini-3.0-flash",
            temperature=0,
            api_key="dummy",
            base_url="http://localhost:3001/openai/v1",
        )

    async def parse_trip(self, query: str, current_state: Optional[TripState] = None) -> TripState:
        today = date.today().isoformat()
        
        # Format the current context for the LLM
        context_json = "{}"
        if current_state:
            context_json = current_state.model_dump_json(indent=2)

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=HUMAN_TEMPLATE.format(
                query=query, 
                today=today,
                current_context=context_json
            )),
        ]

        response = await self.llm.ainvoke(messages)
        raw = response.content.strip()

        # Clean markdown if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            data = json.loads(raw)
            # Ensure travel_class is uppercase for consistency with our schema
            if data["details"].get("travel_class"):
                data["details"]["travel_class"] = data["details"]["travel_class"].upper()
            
            return TripState(**data)
        except Exception as e:
            print(f"[NLP ERROR] Failed to parse LLM response: {e}")
            print(f"Raw response was: {raw}")
            # Fallback to empty state if LLM fails
            return current_state or TripState(details=TripDetails())


nlp_parser = NLPParser()
