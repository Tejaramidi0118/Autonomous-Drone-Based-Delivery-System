from typing import Any, Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=6)
    role: str = "customer"


class LoginRequest(BaseModel):
    email: str
    password: str


class DroneCreate(BaseModel):
    model: str
    max_payload: float
    max_range: float
    battery_capacity: float
    current_battery: float
    latitude: float
    longitude: float
    dark_store_id: Optional[int] = None
    status: str = "idle"


class DroneUpdate(BaseModel):
    model: Optional[str] = None
    max_payload: Optional[float] = None
    max_range: Optional[float] = None
    battery_capacity: Optional[float] = None
    current_battery: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    dark_store_id: Optional[int] = None
    status: Optional[str] = None


class ZoneCreate(BaseModel):
    name: str
    zone_type: str
    coordinates: list[list[float]]


class OrderCreate(BaseModel):
    order_type: str
    payload_weight: float = 1.0
    priority: bool = False
    fragile: bool = False
    pickup_lat: Optional[float] = None
    pickup_lng: Optional[float] = None
    dropoff_lat: float
    dropoff_lng: float
    items: list[dict[str, Any]] = []


class SimulationUpdate(BaseModel):
    failure_probability: float = 0.05
    telemetry_interval: int = 2
    max_orders: int = 30
