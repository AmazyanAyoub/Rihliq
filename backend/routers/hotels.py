from fastapi import APIRouter, HTTPException
from typing import List

from models.schemas import HotelSearchRequest, Hotel
from services.hotel_service import search_hotels

router = APIRouter()


@router.post("/search", response_model=List[Hotel])
async def search_hotels_endpoint(request: HotelSearchRequest):
    try:
        hotels = await search_hotels(request)
        return hotels
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hotel search failed: {str(e)}")
