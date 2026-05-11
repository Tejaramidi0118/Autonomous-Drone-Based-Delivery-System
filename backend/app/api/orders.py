from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.database.session import get_db
from app.models import Order, User
from app.schemas.common import OrderCreate
from app.services.orders import create_order
from app.utils.geo import haversine_km


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/create")
async def create(payload: OrderCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = await create_order(db, user.id, payload)
    return serialize_order(order)


@router.get("/list")
def list_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Order)
    if user.role != "admin":
        query = query.filter(Order.customer_id == user.id)
    return [serialize_order(o) for o in query.order_by(Order.created_at.desc()).all()]


@router.get("/status/{order_id}")
def order_status(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or (user.role != "admin" and order.customer_id != user.id):
        raise HTTPException(status_code=404, detail="Order not found")
    return serialize_order(order)


def serialize_order(order: Order) -> dict:
    route_points = order.route_points or []
    distance_km = sum(haversine_km(a[0], a[1], b[0], b[1]) for a, b in zip(route_points, route_points[1:]))
    return {
        "id": order.id,
        "order_type": order.order_type,
        "status": order.status,
        "dark_store_id": order.dark_store_id,
        "payload_weight": order.payload_weight,
        "priority": order.priority,
        "fragile": order.fragile,
        "pickup_lat": order.pickup_lat,
        "pickup_lng": order.pickup_lng,
        "dropoff_lat": order.dropoff_lat,
        "dropoff_lng": order.dropoff_lng,
        "eta_minutes": order.eta_minutes,
        "predicted_battery_usage": round(order.predicted_battery_usage or 0, 1),
        "route_points": route_points,
        "distance_km": round(distance_km, 2),
        "items": order.items,
        "drone_id": order.assignment.drone_id if order.assignment else None,
        "created_at": order.created_at.isoformat(),
    }
