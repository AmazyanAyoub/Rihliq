import json
from datetime import date
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.schemas import TripDetails


SYSTEM_PROMPT = "You are a JSON data extractor. You only output valid JSON objects. You never write prose, explanations, or markdown."

HUMAN_TEMPLATE = """Extract the trip details from the text below and return a single JSON object.

Text: "{query}"

Return this exact JSON structure (no extra fields, no explanation):
{{
  "origin": "departure city",
  "destination": "destination city",
  "departure_date": "YYYY-MM-DD",
  "return_date": "YYYY-MM-DD or null",
  "num_travelers": 1,
  "preferences": [],
  "budget": "budget or mid-range or luxury or null",
  "trip_type": "leisure or business or adventure or romantic or null"
}}

Today is {today}. Use it to resolve relative dates.
Output only the JSON object:"""


class NLPParser:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gemini-3.0-flash",
            temperature=0,
            api_key="dummy",
            base_url="http://localhost:3001/openai/v1",
        )

    async def parse_trip(self, query: str) -> TripDetails:
        today = date.today().isoformat()

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=HUMAN_TEMPLATE.format(query=query, today=today)),
        ]

        response = await self.llm.ainvoke(messages)
        raw = response.content.strip()

        print(f"[NLP PARSER] Raw response: {repr(raw)}")

        # Strip markdown code blocks if the model wraps output
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)
        return TripDetails(**data)


nlp_parser = NLPParser()
