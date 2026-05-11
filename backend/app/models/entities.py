from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), default="customer", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="customer")


class DarkStore(Base):
    __tablename__ = "dark_stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=False)
    inventory_capacity = Column(Integer, default=0)
    charging_slots = Column(Integer, default=0)
    active_drones = Column(Integer, default=0)
    available_stock = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    location = Column(Geometry("POINT", srid=4326))

    drones = relationship("Drone", back_populates="dark_store")
    orders = relationship("Order", back_populates="dark_store")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    category = Column(String(80), nullable=False)
    price = Column(Float, nullable=False)
    weight_kg = Column(Float, default=0.2)
    stock = Column(Integer, default=100)
    dark_store_id = Column(Integer, ForeignKey("dark_stores.id"), nullable=True)


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dark_store_id = Column(Integer, ForeignKey("dark_stores.id"), nullable=True)
    order_type = Column(String(30), nullable=False)
    status = Column(String(40), default="Pending")
    payload_weight = Column(Float, default=1.0)
    priority = Column(Boolean, default=False)
    fragile = Column(Boolean, default=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)
    dropoff_lat = Column(Float, nullable=False)
    dropoff_lng = Column(Float, nullable=False)
    eta_minutes = Column(Float, default=0)
    predicted_battery_usage = Column(Float, default=0)
    route = Column(Geometry("LINESTRING", srid=4326), nullable=True)
    route_points = Column(JSON, default=list)
    items = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    customer = relationship("User", back_populates="orders")
    dark_store = relationship("DarkStore", back_populates="orders")
    assignment = relationship("Assignment", back_populates="order", uselist=False)


class Drone(Base):
    __tablename__ = "drones"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String(120), nullable=False)
    max_payload = Column(Float, nullable=False)
    max_range = Column(Float, nullable=False)
    battery_capacity = Column(Float, nullable=False)
    current_battery = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(40), default="idle")
    dark_store_id = Column(Integer, ForeignKey("dark_stores.id"), nullable=True)
    location = Column(Geometry("POINT", srid=4326))

    dark_store = relationship("DarkStore", back_populates="drones")
    assignments = relationship("Assignment", back_populates="drone")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    score = Column(Float, default=0)
    eta_minutes = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="assignment")
    drone = relationship("Drone", back_populates="assignments")


class AirspaceZone(Base):
    __tablename__ = "airspace_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    zone_type = Column(String(60), nullable=False)
    polygon = Column(Geometry("POLYGON", srid=4326), nullable=False)
    coordinates = Column(JSON, default=list)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)
    drone_id = Column(Integer, ForeignKey("drones.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    battery = Column(Float, nullable=False)
    speed = Column(Float, default=0)
    status = Column(String(40), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    location = Column(Geometry("POINT", srid=4326))


class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    wind_speed = Column(Float, default=0)
    temperature = Column(Float, default=28)
    humidity = Column(Float, default=55)
    source = Column(String(60), default="synthetic")
    created_at = Column(DateTime, default=datetime.utcnow)


class SimulationConfig(Base):
    __tablename__ = "simulation_configs"

    id = Column(Integer, primary_key=True, index=True)
    running = Column(Boolean, default=False)
    failure_probability = Column(Float, default=0.05)
    telemetry_interval = Column(Integer, default=2)
    max_orders = Column(Integer, default=30)
    notes = Column(Text, default="")
