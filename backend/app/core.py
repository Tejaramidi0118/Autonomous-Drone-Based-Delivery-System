from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Quick Delivery Service"
    database_url: str = "postgresql://drone:drone@localhost:5432/drone_delivery"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-this-secret-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    openweather_api_key: str = ""
    hyderabad_min_lat: float = 17.20
    hyderabad_max_lat: float = 17.62
    hyderabad_min_lng: float = 78.20
    hyderabad_max_lng: float = 78.68

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
