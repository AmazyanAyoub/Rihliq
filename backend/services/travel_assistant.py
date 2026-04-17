import logging
from typing import List, AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from models.schemas import ChatMessage, TripDetails

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Rihliq, an expert AI travel planning assistant.
You help users plan trips by giving concrete, actionable travel advice.

When you have trip context (flights, hotels, destination), use it to personalize your answers.
Be friendly, concise, and specific. Always suggest real tips: best neighborhoods, local food,
transport options, packing advice, visa requirements, weather, and hidden gems.

If the user has no trip context yet, ask them where they want to go and help them plan from scratch."""


def _build_system_with_context(trip: TripDetails | None) -> str:
    if not trip:
        return SYSTEM_PROMPT

    context_block = f"""
Current trip context:
- From: {trip.origin}
- To: {trip.destination}
- Departure: {trip.departure_date}
- Return: {trip.return_date or "One-way"}
- Travelers: {trip.num_travelers}
- Budget: {trip.budget or "Not specified"}
- Trip type: {trip.trip_type or "Not specified"}
- Preferences: {", ".join(trip.preferences) if trip.preferences else "None"}
"""
    return SYSTEM_PROMPT + "\n" + context_block


def _build_messages(
    message: str,
    trip_context: TripDetails | None,
    history: List[ChatMessage],
) -> list:
    messages = [SystemMessage(content=_build_system_with_context(trip_context))]

    for msg in history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))

    messages.append(HumanMessage(content=message))
    return messages


class TravelAssistant:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gemini-3.0-flash",
            temperature=0.7,
            api_key="dummy",
            base_url="http://localhost:3001/openai/v1",
            streaming=True,
        )

    async def stream(
        self,
        message: str,
        trip_context: TripDetails | None,
        history: List[ChatMessage],
    ) -> AsyncGenerator[str, None]:
        messages = _build_messages(message, trip_context, history)

        try:
            async for chunk in self.llm.astream(messages):
                token = chunk.content
                if token:
                    yield token
        except Exception as e:
            logger.error(f"[TRAVEL ASSISTANT] Streaming error: {type(e).__name__}: {e}")
            yield f"\n\n[Error: {str(e)}]"


travel_assistant = TravelAssistant()
