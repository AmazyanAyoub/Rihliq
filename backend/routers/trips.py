from fastapi import APIRouter, HTTPException
from models.schemas import TripParseRequest, AgentState
from services.travel_assistant import travel_assistant

router = APIRouter()

@router.post("/process")
async def process_trip(request: TripParseRequest):
    try:
        # Initial processing of a natural language query
        state = await travel_assistant.process_message(request.query, thread_id="default")
        return state
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process trip: {str(e)}")
