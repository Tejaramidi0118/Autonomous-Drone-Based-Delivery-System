import asyncio
import random
from datetime import datetime
from geoalchemy2.functions import ST_GeomFromText
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models import Assignment, Drone, Order, SimulationConfig, Telemetry
from app.utils.geo import haversine_km, point_wkt
from app.websocket.manager import telemetry_manager


class SimulationEngine:
    def __init__(self):
        self.running = False
        self.task: asyncio.Task | None = None

    def start(self) -> None:
        self.running = True
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        self.running = False

    async def _loop(self) -> None:
        while self.running:
            db = SessionLocal()
            try:
                config = db.query(SimulationConfig).first()
                interval = config.telemetry_interval if config else 2
                failure_probability = config.failure_probability if config else 0.05
                active = db.query(Order).filter(Order.status.in_(["Assigned", "Taking Off", "In Flight", "Delivering", "Reassigned"])).all()
                for order in active:
                    await self._advance_order(db, order, failure_probability)
                db.commit()
            finally:
                db.close()
            await asyncio.sleep(interval)

    async def _advance_order(self, db: Session, order: Order, failure_probability: float) -> None:
        assignment = db.query(Assignment).filter(Assignment.order_id == order.id).first()
        if not assignment:
            return
        drone = assignment.drone
        points = order.route_points or [[order.pickup_lat, order.pickup_lng], [order.dropoff_lat, order.dropoff_lng]]
        idx = getattr(order, "_sim_index", None)
        if idx is None:
            idx = _current_index(points, drone.latitude, drone.longitude)
        idx = min(idx + 1, len(points) - 1)
        order._sim_index = idx

        if random.random() < failure_probability / 20:
            order.status = "Failed"
            drone.status = "failed"
            await telemetry_manager.broadcast(order.id, _payload(order, drone, "failure"))
            return

        drone.latitude, drone.longitude = points[idx]
        drone.current_battery = max(0, drone.current_battery - max(0.8, order.predicted_battery_usage / max(1, len(points))))
        drone.location = ST_GeomFromText(point_wkt(drone.latitude, drone.longitude), 4326)
        if idx == 1:
            order.status = "Taking Off"
            drone.status = "taking_off"
        elif idx < len(points) - 1:
            order.status = "In Flight"
            drone.status = "in_flight"
        else:
            order.status = "Delivered"
            drone.status = "returning"
            order.delivered_at = datetime.utcnow()

        telemetry = Telemetry(
            drone_id=drone.id,
            order_id=order.id,
            latitude=drone.latitude,
            longitude=drone.longitude,
            battery=drone.current_battery,
            speed=38,
            status=order.status,
            location=ST_GeomFromText(point_wkt(drone.latitude, drone.longitude), 4326),
        )
        db.add(telemetry)
        await telemetry_manager.broadcast(order.id, _payload(order, drone, "telemetry"))


def _current_index(points: list[list[float]], lat: float, lng: float) -> int:
    distances = [(abs(p[0] - lat) + abs(p[1] - lng), idx) for idx, p in enumerate(points)]
    return min(distances)[1] if distances else 0


def _payload(order: Order, drone: Drone, event: str) -> dict:
    route = order.route_points or []
    distance_km = sum(haversine_km(a[0], a[1], b[0], b[1]) for a, b in zip(route, route[1:]))
    return {
        "event": event,
        "order_id": order.id,
        "drone_id": drone.id,
        "latitude": drone.latitude,
        "longitude": drone.longitude,
        "battery": round(drone.current_battery, 1),
        "speed": 38,
        "status": order.status,
        "route": route,
        "distance_km": round(distance_km, 2),
        "eta_minutes": order.eta_minutes,
    }


simulation_engine = SimulationEngine()
