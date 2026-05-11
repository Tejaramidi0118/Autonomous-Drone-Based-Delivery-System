import json
import random
import redis
from redis.exceptions import RedisError
import httpx
from app.core import get_settings


settings = get_settings()
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


async def get_weather(lat: float, lng: float) -> dict:
    cache_key = f"weather:{round(lat, 2)}:{round(lng, 2)}"
    cached = None
    try:
        cached = redis_client.get(cache_key)
    except RedisError:
        cached = None
    if cached:
        return json.loads(cached)

    data = {
        "wind_speed": round(random.uniform(2.0, 8.0), 1),
        "temperature": round(random.uniform(25.0, 35.0), 1),
        "humidity": round(random.uniform(45.0, 75.0), 1),
        "source": "synthetic",
    }
    if settings.openweather_api_key:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lng, "appid": settings.openweather_api_key, "units": "metric"}
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(url, params=params)
            if response.is_success:
                body = response.json()
                data = {
                    "wind_speed": body.get("wind", {}).get("speed", data["wind_speed"]),
                    "temperature": body.get("main", {}).get("temp", data["temperature"]),
                    "humidity": body.get("main", {}).get("humidity", data["humidity"]),
                    "source": "openweather",
                }
    try:
        redis_client.setex(cache_key, 900, json.dumps(data))
    except RedisError:
        pass
    return data
