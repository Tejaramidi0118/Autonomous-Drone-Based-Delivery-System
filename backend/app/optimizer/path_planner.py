import heapq
from app.core import get_settings


settings = get_settings()


class AStarPlanner:
    def __init__(self, obstacles: list[list[list[float]]] | None = None, grid_size: int = 56):
        self.obstacles = obstacles or []
        self.grid_size = grid_size

    def _to_cell(self, lat: float, lng: float) -> tuple[int, int]:
        x = round((lng - settings.hyderabad_min_lng) / (settings.hyderabad_max_lng - settings.hyderabad_min_lng) * self.grid_size)
        y = round((lat - settings.hyderabad_min_lat) / (settings.hyderabad_max_lat - settings.hyderabad_min_lat) * self.grid_size)
        return max(0, min(self.grid_size, x)), max(0, min(self.grid_size, y))

    def _to_coord(self, cell: tuple[int, int]) -> list[float]:
        x, y = cell
        lng = settings.hyderabad_min_lng + (x / self.grid_size) * (settings.hyderabad_max_lng - settings.hyderabad_min_lng)
        lat = settings.hyderabad_min_lat + (y / self.grid_size) * (settings.hyderabad_max_lat - settings.hyderabad_min_lat)
        return [round(lat, 6), round(lng, 6)]

    def _blocked(self, cell: tuple[int, int]) -> bool:
        lat, lng = self._to_coord(cell)
        return any(_point_in_poly(lat, lng, poly) for poly in self.obstacles)

    def plan(self, start: tuple[float, float], goal: tuple[float, float]) -> list[list[float]]:
        start_cell = self._to_cell(*start)
        goal_cell = self._to_cell(*goal)
        frontier = [(0, start_cell)]
        came_from = {start_cell: None}
        cost_so_far = {start_cell: 0}
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]

        while frontier:
            _, current = heapq.heappop(frontier)
            if current == goal_cell:
                break
            for dx, dy in directions:
                nxt = (current[0] + dx, current[1] + dy)
                if nxt[0] < 0 or nxt[1] < 0 or nxt[0] > self.grid_size or nxt[1] > self.grid_size or self._blocked(nxt):
                    continue
                new_cost = cost_so_far[current] + (1.4 if dx and dy else 1)
                if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                    cost_so_far[nxt] = new_cost
                    priority = new_cost + abs(goal_cell[0] - nxt[0]) + abs(goal_cell[1] - nxt[1])
                    heapq.heappush(frontier, (priority, nxt))
                    came_from[nxt] = current

        if goal_cell not in came_from:
            return [[start[0], start[1]], [goal[0], goal[1]]]

        path = []
        current = goal_cell
        while current:
            path.append(self._to_coord(current))
            current = came_from[current]
        path.reverse()
        path[0] = [start[0], start[1]]
        path[-1] = [goal[0], goal[1]]
        return _simplify(path)


def _point_in_poly(lat: float, lng: float, poly: list[list[float]]) -> bool:
    inside = False
    j = len(poly) - 1
    for i, point in enumerate(poly):
        yi, xi = point
        yj, xj = poly[j]
        crosses = (xi > lng) != (xj > lng) and lat < (yj - yi) * (lng - xi) / ((xj - xi) or 1e-9) + yi
        if crosses:
            inside = not inside
        j = i
    return inside


def _simplify(points: list[list[float]]) -> list[list[float]]:
    if len(points) <= 18:
        return points
    step = max(1, len(points) // 16)
    sampled = points[::step]
    if sampled[-1] != points[-1]:
        sampled.append(points[-1])
    return sampled
