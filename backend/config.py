from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # AI
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Flight API
    duffel_access_token: str = ""

    # Hotel API
    rapidapi_key: str = ""

    # Restaurant API
    foursquare_api_key: str = ""
    google_maps_api_key: str = ""

    # Optional scraping
    brightdata_api_key: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    google_api_key: str = ""  # For Google Places in restaurant service, and potentially other Google APIs

    GROQ_API_KEY: str = ""  # For Groq vector search if used in the future

    # App
    frontend_url: str = "http://localhost:5173"


    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"



@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
