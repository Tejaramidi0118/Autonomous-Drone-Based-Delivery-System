from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import require_admin
from app.database.session import get_db
from app.models import DarkStore, Drone, Order, SimulationConfig, Telemetry
from app.schemas.common import SimulationUpdate
from app.simulation.engine import simulation_engine


router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/start")
def start_simulation(payload: SimulationUpdate, _=Depends(require_admin), db: Session = Depends(get_db)):
    config = db.query(SimulationConfig).first() or SimulationConfig()
    config.running = True
    config.failure_probability = payload.failure_probability
    config.telemetry_interval = payload.telemetry_interval
    config.max_orders = payload.max_orders
    db.add(config)
    db.commit()
    simulation_engine.start()
    return {"running": True}


@router.post("/stop")
def stop_simulation(_=Depends(require_admin), db: Session = Depends(get_db)):
    config = db.query(SimulationConfig).first() or SimulationConfig()
    config.running = False
    db.add(config)
    db.commit()
    simulation_engine.stop()
    return {"running": False}


@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    c = db.query(SimulationConfig).first()
    return {"running": bool(c and c.running), "failure_probability": c.failure_probability if c else 0.05, "telemetry_interval": c.telemetry_interval if c else 2, "max_orders": c.max_orders if c else 30}


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    total = db.query(Order).count()
    failed = db.query(Order).filter(Order.status == "Failed").count()
    delivered = db.query(Order).filter(Order.status == "Delivered").count()
    active = db.query(Order).filter(Order.status.in_(["Assigned", "Taking Off", "In Flight", "Delivering"])).count()
    drones = db.query(Drone).count()
    avg_battery = db.query(func.avg(Drone.current_battery)).scalar() or 0
    stores = db.query(DarkStore).all()
    hub_stats = []
    for s in stores:
        hub_orders = db.query(Order).filter(Order.dark_store_id == s.id).count()
        hub_stats.append({
            "name": s.name,
            "active_drones": db.query(Drone).filter(Drone.dark_store_id == s.id, Drone.status != "idle").count(),
            "inventory_usage": s.inventory_capacity - s.available_stock,
            "order_density": hub_orders,
            "battery_utilization": round(100 - (db.query(func.avg(Drone.current_battery)).filter(Drone.dark_store_id == s.id).scalar() or 0), 1),
        })
    busiest = max(hub_stats, key=lambda h: h["order_density"], default={"name": "None"})
    return {
        "total_drones": drones,
        "active_deliveries": active,
        "failed_deliveries": failed,
        "delivered_orders": delivered,
        "average_battery": round(avg_battery, 1),
        "failure_rate": round((failed / total) * 100, 1) if total else 0,
        "compliance_rate": 100,
        "busiest_hub": busiest["name"],
        "hub_stats": hub_stats,
        "telemetry_points": db.query(Telemetry).count(),
    }
