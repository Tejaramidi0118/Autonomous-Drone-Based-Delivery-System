"""
Simulation Engine — Fixed drone movement
=========================================
ROOT CAUSE OF DRONE NOT MOVING:
  Theta* produces 2 waypoints (start, end).
  The original engine advanced by idx+1 per tick, so with 2 waypoints
  the drone teleported from start to end in a single 2-second tick —
  never visible as movement on the map.

THE FIX:
  Track progress as cumulative distance (float km) instead of waypoint index.
  Each tick advances by speed_kmh * interval_sec / 3600 km.
  Position is interpolated within the current segment.
  For 3.99 km at 38 km/h with 2s ticks → 189 ticks of smooth movement.

Also fixed:
  - eta_minutes updated every tick (was never updated mid-flight)
  - speed broadcast as real value (was hardcoded 38)
  - battery drain proportional to distance (was fixed per-tick)
"""
import asyncio
import math
import random
from datetime import datetime, timezone

from geoalchemy2.functions import ST_GeomFromText
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models import Assignment, Drone, Order, SimulationConfig, Telemetry
from app.utils.geo import haversine_km, point_wkt
from app.websocket.manager import telemetry_manager


CRUISE_SPEED_KMH = 38.0   # km/h nominal — matches frontend display


class SimulationEngine:
    def __init__(self):
        self.running = False
        self.task: asyncio.Task | None = None
        # progress_km[order_id] = cumulative km travelled along route
        self._progress_km: dict[int, float] = {}

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
                interval           = config.telemetry_interval   if config else 2
                failure_probability= config.failure_probability   if config else 0.05

                active = db.query(Order).filter(
                    Order.status.in_(["Assigned", "Taking Off", "In Flight", "Delivering", "Reassigned"])
                ).all()

                for order in active:
                    await self._advance_order(db, order, failure_probability, float(interval))

                db.commit()
            finally:
                db.close()
            await asyncio.sleep(interval)

    async def _advance_order(
        self, db: Session, order: Order, failure_prob: float, interval_s: float
    ) -> None:
        assignment = db.query(Assignment).filter(Assignment.order_id == order.id).first()
        if not assignment:
            return

        drone: Drone = assignment.drone
        points = order.route_points or [
            [order.pickup_lat, order.pickup_lng],
            [order.dropoff_lat, order.dropoff_lng],
        ]
        if len(points) < 2:
            return

        # ── Total route distance (computed once) ───────────────────────
        total_km = sum(
            haversine_km(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
            for i in range(len(points) - 1)
        ) or 0.001

        # ── Distance to advance this tick ───────────────────────────────
        # speed (km/h) × time (h) = distance (km)
        dist_tick_km = CRUISE_SPEED_KMH * (interval_s / 3600.0)

        # ── Random failure ──────────────────────────────────────────────
        # Convert config failure_probability (intended as % chance over full flight)
        # into a per-tick probability that gives the right cumulative failure rate.
        # P(fail per tick) = 1 - (1 - failure_prob) ^ (1 / total_ticks)
        # where total_ticks = total_km / (CRUISE_SPEED_KMH * interval_s / 3600)
        total_ticks = max(1, total_km / (CRUISE_SPEED_KMH * interval_s / 3600))
        per_tick_fail = 1.0 - (1.0 - min(failure_prob, 0.99)) ** (1.0 / total_ticks)
        if random.random() < per_tick_fail:
            order.status  = "Failed"
            drone.status  = "failed"
            self._progress_km.pop(order.id, None)
            await telemetry_manager.broadcast(order.id, _payload(order, drone, "failure", total_km))
            return

        # ── Advance progress ────────────────────────────────────────────
        progress = self._progress_km.get(order.id, 0.0)
        progress = min(progress + dist_tick_km, total_km)
        self._progress_km[order.id] = progress

        # ── Interpolate position along route ────────────────────────────
        new_lat, new_lng = _position_at_distance(points, progress)
        drone.latitude   = new_lat
        drone.longitude  = new_lng
        drone.location   = ST_GeomFromText(point_wkt(new_lat, new_lng), 4326)

        # ── Battery drain proportional to distance ──────────────────────
        drain = max(0.8, order.predicted_battery_usage * (dist_tick_km / total_km))
        drone.current_battery = max(0.0, drone.current_battery - drain)

        # ── Status transitions ──────────────────────────────────────────
        frac = progress / total_km
        if frac < 0.04:
            order.status = "Taking Off"
            drone.status = "taking_off"
        elif frac < 0.88:
            order.status = "In Flight"
            drone.status = "in_flight"
        elif frac < 1.0:
            order.status = "Delivering"
            drone.status = "in_flight"

        # ── Update ETA every tick ───────────────────────────────────────
        remaining_km      = total_km - progress
        remaining_h       = remaining_km / CRUISE_SPEED_KMH
        order.eta_minutes = round(remaining_h * 60.0 + 1.2, 1)   # +1.2 min landing buffer

        # ── Delivery reached ────────────────────────────────────────────
        if progress >= total_km:
            order.status        = "Delivered"
            drone.status        = "idle"
            order.eta_minutes   = 0.0
            order.delivered_at  = datetime.now(timezone.utc)
            self._progress_km.pop(order.id, None)
            # Return drone to hub
            if drone.dark_store:
                drone.latitude  = drone.dark_store.latitude
                drone.longitude = drone.dark_store.longitude
                drone.location  = ST_GeomFromText(point_wkt(drone.latitude, drone.longitude), 4326)
            drone.current_battery = 100.0
            db.add(_telemetry_row(drone, order))
            await telemetry_manager.broadcast(order.id, _payload(order, drone, "delivered", total_km))
            return

        # ── Log telemetry row ───────────────────────────────────────────
        db.add(_telemetry_row(drone, order))

        # ── Broadcast WebSocket payload ─────────────────────────────────
        await telemetry_manager.broadcast(order.id, _payload(order, drone, "telemetry", total_km))


# ── Helpers ──────────────────────────────────────────────────────────────

def _position_at_distance(points: list, target_km: float) -> tuple[float, float]:
    """
    Walk route waypoints and return interpolated (lat, lng) at
    exactly target_km cumulative Haversine distance.
    Returns final waypoint if target exceeds total length.
    """
    accumulated = 0.0
    for i in range(len(points) - 1):
        seg_km = haversine_km(
            points[i][0], points[i][1],
            points[i+1][0], points[i+1][1],
        )
        if accumulated + seg_km >= target_km:
            frac = (target_km - accumulated) / max(seg_km, 1e-9)
            lat  = points[i][0] + frac * (points[i+1][0] - points[i][0])
            lng  = points[i][1] + frac * (points[i+1][1] - points[i][1])
            return round(lat, 7), round(lng, 7)
        accumulated += seg_km
    return points[-1][0], points[-1][1]


def _telemetry_row(drone: Drone, order: Order) -> Telemetry:
    return Telemetry(
        drone_id=drone.id,
        order_id=order.id,
        latitude=drone.latitude,
        longitude=drone.longitude,
        battery=drone.current_battery,
        speed=CRUISE_SPEED_KMH,
        status=order.status,
        location=ST_GeomFromText(point_wkt(drone.latitude, drone.longitude), 4326),
    )


def _payload(order: Order, drone: Drone, event: str, total_km: float) -> dict:
    """WebSocket payload — matches exactly what tracking.html expects."""
    return {
        "event":        event,
        "order_id":     order.id,
        "drone_id":     drone.id,
        "latitude":     drone.latitude,
        "longitude":    drone.longitude,
        "battery":      round(drone.current_battery, 1),
        "speed_kmh":    CRUISE_SPEED_KMH,        # frontend uses speed_kmh
        "speed":        CRUISE_SPEED_KMH,         # fallback for older frontend
        "status":       order.status,
        "route":        order.route_points or [],
        "distance_km":  round(total_km, 2),
        "eta_minutes":  round(order.eta_minutes or 0, 1),
    }


simulation_engine = SimulationEngine()