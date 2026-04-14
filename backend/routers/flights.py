from fastapi import APIRouter, HTTPException
from typing import List

from models.schemas import FlightSearchRequest, Flight
from services.flight_service import search_flights

router = APIRouter()


@router.post("/search", response_model=List[Flight])
async def search_flights_endpoint(request: FlightSearchRequest):
    try:
        flights = await search_flights(request)
        return flights
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Flight search failed: {str(e)}")
