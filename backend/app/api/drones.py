from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.functions import ST_GeomFromText
from sqlalchemy.orm import Session
from app.api.deps import require_admin
from app.database.session import get_db
from app.models import Drone
from app.schemas.common import DroneCreate, DroneUpdate
from app.utils.geo import point_wkt


router = APIRouter(prefix="/drones", tags=["drones"])


@router.get("")
def list_drones(db: Session = Depends(get_db)):
    return [_drone(d) for d in db.query(Drone).order_by(Drone.id).all()]


@router.post("/add")
def add_drone(payload: DroneCreate, _=Depends(require_admin), db: Session = Depends(get_db)):
    drone = Drone(**payload.model_dump(), location=ST_GeomFromText(point_wkt(payload.latitude, payload.longitude), 4326))
    db.add(drone)
    db.commit()
    db.refresh(drone)
    return _drone(drone)


@router.put("/update/{drone_id}")
def update_drone(drone_id: int, payload: DroneUpdate, _=Depends(require_admin), db: Session = Depends(get_db)):
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(drone, key, value)
    drone.location = ST_GeomFromText(point_wkt(drone.latitude, drone.longitude), 4326)
    db.commit()
    return _drone(drone)


@router.delete("/delete/{drone_id}")
def delete_drone(drone_id: int, _=Depends(require_admin), db: Session = Depends(get_db)):
    drone = db.query(Drone).filter(Drone.id == drone_id).first()
    if not drone:
        raise HTTPException(status_code=404, detail="Drone not found")
    db.delete(drone)
    db.commit()
    return {"ok": True}


def _drone(d: Drone) -> dict:
    return {
        "id": d.id,
        "model": d.model,
        "max_payload": d.max_payload,
        "max_range": d.max_range,
        "battery_capacity": d.battery_capacity,
        "current_battery": d.current_battery,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "status": d.status,
        "dark_store_id": d.dark_store_id,
    }
