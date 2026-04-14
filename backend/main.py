from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from routers import trips, flights, hotels, restaurants, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("RIHLIQ starting...")
    yield
    print("RIHLIQ shutting down...")


app = FastAPI(
    title="RIHLIQ - AI Travel Planner",
    description="Intelligent travel planning with AI-powered search and assistance",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trips.router,       prefix="/api/trip",        tags=["trips"])
app.include_router(flights.router,     prefix="/api/flights",     tags=["flights"])
app.include_router(hotels.router,      prefix="/api/hotels",      tags=["hotels"])
app.include_router(restaurants.router, prefix="/api/restaurants", tags=["restaurants"])
app.include_router(chat.router,        prefix="/api/chat",        tags=["chat"])


@app.get("/api/health", response_model=dict)
async def health_check():
    return {"status": "ok", "message": "AI Travel Planner API is running"}
