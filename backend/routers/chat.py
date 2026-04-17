from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.schemas import ChatRequest
from services.travel_assistant import travel_assistant

router = APIRouter()


async def _sse_generator(message: str, request: ChatRequest):
    async for token in travel_assistant.stream(
        message=message,
        trip_context=request.trip_context,
        history=request.history,
    ):
        # SSE format: each chunk prefixed with "data: " and ending with double newline
        yield f"data: {token}\n\n"
    yield "data: [DONE]\n\n"


@router.post("/travel")
async def travel_chat(request: ChatRequest):
    return StreamingResponse(
        _sse_generator(request.message, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disables Nginx buffering if behind a proxy
        },
    )
