from fastapi import APIRouter, HTTPException
from typing import List

from models.schemas import RestaurantSearchRequest, Restaurant
from services.restaurant_service import search_restaurants

router = APIRouter()


@router.post("/search", response_model=List[Restaurant])
async def search_restaurants_endpoint(request: RestaurantSearchRequest):
    try:
        restaurants = await search_restaurants(request)
        return restaurants
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restaurant search failed: {str(e)}")
