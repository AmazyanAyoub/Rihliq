from fastapi import APIRouter, HTTPException
from models.schemas import TripParseRequest, TripDetails
from services.nlp_parser import nlp_parser

router = APIRouter()


@router.post("/parse", response_model=TripDetails)
async def parse_trip(request: TripParseRequest):
    try:
        trip = await nlp_parser.parse_trip(request.query)
        return trip
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse trip: {str(e)}")
