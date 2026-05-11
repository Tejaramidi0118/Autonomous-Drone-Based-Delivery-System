from ortools.linear_solver import pywraplp
from app.models import Drone
from app.utils.geo import haversine_km


def assign_best_drone(drones: list[Drone], start_lat: float, start_lng: float, payload: float, battery_usage: float) -> tuple[Drone | None, float]:
    candidates = [
        d for d in drones
        if d.status in ("idle", "charging") and d.max_payload >= payload and d.current_battery > battery_usage + 12
    ]
    if not candidates:
        return None, 0

    solver = pywraplp.Solver.CreateSolver("SCIP")
    variables = [solver.BoolVar(f"drone_{d.id}") for d in candidates]
    solver.Add(sum(variables) == 1)
    objective = solver.Objective()
    for var, drone in zip(variables, candidates):
        distance_to_pickup = haversine_km(drone.latitude, drone.longitude, start_lat, start_lng)
        cost = distance_to_pickup * 4 + (100 - drone.current_battery) * 0.5
        objective.SetCoefficient(var, cost)
    objective.SetMinimization()
    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        return candidates[0], 0
    for var, drone in zip(variables, candidates):
        if var.solution_value() > 0.5:
            return drone, objective.Value()
    return None, 0
