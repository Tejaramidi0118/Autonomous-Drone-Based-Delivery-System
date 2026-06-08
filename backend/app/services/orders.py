from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_GeomFromText, ST_Intersects
from app.ml.battery_model import predict_battery_usage
from app.services.eta_calculator import compute_eta_minutes
from app.models import AirspaceZone, Assignment, DarkStore, Drone, Order, Product
from app.optimizer.assignment import assign_best_drone
from app.optimizer.path_planner import AStarPlanner
from app.schemas.common import OrderCreate
from app.services.weather import get_weather
from app.utils.geo import haversine_km, is_in_hyderabad, linestring_wkt


async def create_order(db: Session, user_id: int, payload: OrderCreate) -> Order:
    if not is_in_hyderabad(payload.dropoff_lat, payload.dropoff_lng):
        raise HTTPException(status_code=400, detail="Dropoff must be within Hyderabad")

    dark_store = None
    pickup_lat = payload.pickup_lat
    pickup_lng = payload.pickup_lng
    if payload.order_type == "grocery":
        dark_store = _nearest_stocked_dark_store(db, payload.dropoff_lat, payload.dropoff_lng)
        pickup_lat, pickup_lng = dark_store.latitude, dark_store.longitude
    elif pickup_lat is None or pickup_lng is None or not is_in_hyderabad(pickup_lat, pickup_lng):
        raise HTTPException(status_code=400, detail="Package pickup must be within Hyderabad")

    zones = db.query(AirspaceZone).filter(AirspaceZone.active.is_(True)).all()
    route_points = AStarPlanner([z.coordinates for z in zones]).plan((pickup_lat, pickup_lng), (payload.dropoff_lat, payload.dropoff_lng))
    distance_km = _route_distance(route_points)
    weather = await get_weather(payload.dropoff_lat, payload.dropoff_lng)
    battery = predict_battery_usage(distance_km, payload.payload_weight, weather["wind_speed"], weather["humidity"], weather["temperature"])
    drones_query = db.query(Drone)
    if dark_store:
        drones_query = drones_query.filter(Drone.dark_store_id == dark_store.id)
    drone, score = assign_best_drone(drones_query.all(), pickup_lat, pickup_lng, payload.payload_weight, battery)

    eta = compute_eta_minutes(
        distance_km=distance_km,
        payload_kg=payload.payload_weight,
        wind_speed_ms=weather["wind_speed"],
        temperature_c=weather["temperature"],
        humidity_pct=weather["humidity"],
        fragile=payload.fragile,
        priority=payload.priority,
    )
    order = Order(
        customer_id=user_id,
        dark_store_id=dark_store.id if dark_store else None,
        order_type=payload.order_type,
        status="Assigned" if drone else "Pending",
        payload_weight=payload.payload_weight,
        priority=payload.priority,
        fragile=payload.fragile,
        pickup_lat=pickup_lat,
        pickup_lng=pickup_lng,
        dropoff_lat=payload.dropoff_lat,
        dropoff_lng=payload.dropoff_lng,
        eta_minutes=eta,
        predicted_battery_usage=battery,
        route_points=route_points,
        route=ST_GeomFromText(linestring_wkt(route_points), 4326),
        items=payload.items,
    )
    db.add(order)
    db.flush()
    if drone:
        drone.status = "assigned"
        assignment = Assignment(order_id=order.id, drone_id=drone.id, score=score, eta_minutes=eta)
        db.add(assignment)
    if dark_store:
        dark_store.available_stock = max(0, dark_store.available_stock - max(1, len(payload.items)))
    db.commit()
    db.refresh(order)
    return order


def validate_route_against_zones(db: Session, order: Order) -> bool:
    invalid = db.query(AirspaceZone).filter(
        AirspaceZone.active.is_(True),
        ST_Intersects(order.route, AirspaceZone.polygon),
    ).first()
    return invalid is None


def complete_order(db: Session, order: Order) -> None:
    order.status = "Delivered"
    order.delivered_at = datetime.utcnow()
    if order.assignment:
        order.assignment.drone.status = "returning"
    db.commit()


def _nearest_stocked_dark_store(db: Session, lat: float, lng: float) -> DarkStore:
    stores = db.query(DarkStore).filter(DarkStore.available_stock > 0).all()
    if not stores:
        raise HTTPException(status_code=409, detail="No dark store has available inventory")
    return min(stores, key=lambda s: haversine_km(s.latitude, s.longitude, lat, lng))


def _route_distance(points: list[list[float]]) -> float:
    return sum(haversine_km(a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:]))
