from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import DarkStore, Drone, Order


router = APIRouter(prefix="/darkstores", tags=["darkstores"])


@router.get("")
def list_darkstores(db: Session = Depends(get_db)):
    stores = db.query(DarkStore).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "address": s.address,
            "inventory_capacity": s.inventory_capacity,
            "charging_slots": s.charging_slots,
            "available_stock": s.available_stock,
            "drone_count": db.query(Drone).filter(Drone.dark_store_id == s.id).count(),
            "active_deliveries": db.query(Order).filter(Order.dark_store_id == s.id, Order.status.in_(["Assigned", "Taking Off", "In Flight", "Delivering"])).count(),
        }
        for s in stores
    ]
