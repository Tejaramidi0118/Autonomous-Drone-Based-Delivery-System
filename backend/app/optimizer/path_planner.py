"""
Theta* Path Planner (Lazy Theta* variant)
==========================================
Replaces the original grid-locked A* implementation with Lazy Theta*,
an any-angle path planning algorithm that finds shorter, smoother paths
without being constrained to the 8-direction grid edges of standard A*.

Algorithm
---------
Lazy Theta* (Nash et al., 2010) is a variant of Theta* (Daniel et al., 2010)
that defers the expensive line-of-sight check from push-time to pop-time.
This reduces total line-of-sight calls while producing paths of equal quality.

Key improvements over the previous A* implementation
-----------------------------------------------------
1. Admissible heuristic: Euclidean distance replaces the inadmissible
   Manhattan heuristic that was used with a grid allowing diagonal movement.
   Manhattan distance overestimates diagonal steps, violating the A* optimality
   condition h(n) <= h*(n).

2. Any-angle paths: Line-of-sight checks allow the planner to shortcut
   across grid cells, connecting any two mutually visible waypoints directly.
   This eliminates the characteristic staircase artefact of grid-locked A*
   and produces paths up to ~13% shorter (Daniel et al., 2010).

3. Natural path smoothing: Because any-angle shortcuts are applied during
   search, the resulting path already has minimal waypoints. No separate
   downsampling step is needed (the old _simplify() approach is removed).

References
----------
[1] Daniel, K., Nash, A., Koenig, S., & Felner, A. (2010).
    Theta*: Any-angle path planning on grids.
    Journal of Artificial Intelligence Research, 39, 533-579.

[2] Nash, A., Koenig, S., & Likhachev, M. (2010).
    Lazy Theta*: Any-angle path planning and pathfinding for smooth
    trajectories in continuous environments.
    Proceedings of the AAAI Conference on Artificial Intelligence.

[3] Nash, A., & Koenig, S. (2013).
    Any-angle path planning.
    AI Magazine, 34(4), 85-107.
"""

from __future__ import annotations

import heapq
import math
from app.core import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Grid constants
# ---------------------------------------------------------------------------
_GRID_SIZE = 56   # 56×56 discrete grid over Hyderabad bounding box


# ---------------------------------------------------------------------------
# Coordinate ↔ cell conversion
# ---------------------------------------------------------------------------

def _to_cell(lat: float, lng: float) -> tuple[int, int]:
    """Convert GPS coordinate to grid cell (x, y)."""
    x = round(
        (lng - settings.hyderabad_min_lng)
        / (settings.hyderabad_max_lng - settings.hyderabad_min_lng)
        * _GRID_SIZE
    )
    y = round(
        (lat - settings.hyderabad_min_lat)
        / (settings.hyderabad_max_lat - settings.hyderabad_min_lat)
        * _GRID_SIZE
    )
    return max(0, min(_GRID_SIZE, x)), max(0, min(_GRID_SIZE, y))


def _to_coord(cell: tuple[int, int]) -> list[float]:
    """Convert grid cell back to [lat, lng] GPS coordinate."""
    x, y = cell
    lng = settings.hyderabad_min_lng + (x / _GRID_SIZE) * (
        settings.hyderabad_max_lng - settings.hyderabad_min_lng
    )
    lat = settings.hyderabad_min_lat + (y / _GRID_SIZE) * (
        settings.hyderabad_max_lat - settings.hyderabad_min_lat
    )
    return [round(lat, 6), round(lng, 6)]


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _euclidean(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Euclidean distance between two grid cells — admissible heuristic."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _point_in_poly(lat: float, lng: float, poly: list[list[float]]) -> bool:
    """
    Ray-casting polygon containment test.
    Polygon vertices are stored as [lat, lng] pairs (SRID 4326).
    """
    inside = False
    j = len(poly) - 1
    for i, point in enumerate(poly):
        yi, xi = point
        yj, xj = poly[j]
        crosses = (xi > lng) != (xj > lng) and (
            lat < (yj - yi) * (lng - xi) / ((xj - xi) or 1e-9) + yi
        )
        if crosses:
            inside = not inside
        j = i
    return inside


def _line_of_sight(
    s: tuple[int, int],
    t: tuple[int, int],
    blocked: set[tuple[int, int]],
) -> bool:
    """
    Integer Bresenham line-of-sight check between grid cells s and t.

    Traverses every grid cell crossed by the straight line segment and
    returns False as soon as a blocked cell is encountered.

    Based on the LOS subroutine described in:
      Daniel et al. (2010), Section 3.1.
    """
    x0, y0 = s
    x1, y1 = t
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if (x0, y0) in blocked:
            return False
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

    return True


# ---------------------------------------------------------------------------
# Planner class
# ---------------------------------------------------------------------------

# 8-connected neighbourhood with step costs
_DIRECTIONS = [
    (1, 0), (-1, 0), (0, 1), (0, -1),   # cardinal  (cost √1)
    (1, 1), (-1, -1), (1, -1), (-1, 1),  # diagonal  (cost √2)
]


class ThetaStarPlanner:
    """
    Any-angle path planner using Lazy Theta*.

    The planner maps the Hyderabad bounding box to a discrete grid,
    marks cells that fall inside active airspace restriction polygons as
    blocked, and searches for a near-shortest any-angle path from start
    to goal using the Lazy Theta* algorithm.

    Parameters
    ----------
    obstacles : list of polygons, each polygon is a list of [lat, lng] pairs
    grid_size : grid resolution (default 56 → 56×56 cells)
    """

    def __init__(
        self,
        obstacles: list[list[list[float]]] | None = None,
        grid_size: int = _GRID_SIZE,
    ) -> None:
        self.obstacles = obstacles or []
        self.grid_size = grid_size
        self._blocked: set[tuple[int, int]] = self._precompute_blocked()

    # ------------------------------------------------------------------
    # Pre-computation
    # ------------------------------------------------------------------

    def _precompute_blocked(self) -> set[tuple[int, int]]:
        """
        Mark every grid cell whose centre falls inside an active
        airspace restriction polygon.

        Pre-computing once per planner instance is more efficient than
        re-running the ray-casting test for every line-of-sight query.
        """
        blocked: set[tuple[int, int]] = set()
        if not self.obstacles:
            return blocked
        for xi in range(self.grid_size + 1):
            for yi in range(self.grid_size + 1):
                lat, lng = _to_coord((xi, yi))
                if any(_point_in_poly(lat, lng, poly) for poly in self.obstacles):
                    blocked.add((xi, yi))
        return blocked

    # ------------------------------------------------------------------
    # Public interface — same signature as the old AStarPlanner.plan()
    # ------------------------------------------------------------------

    def plan(
        self,
        start: tuple[float, float],
        goal: tuple[float, float],
    ) -> list[list[float]]:
        """
        Compute a near-shortest any-angle path from start to goal,
        routing around all active airspace restriction zones.

        Parameters
        ----------
        start : (lat, lng) of the pickup point
        goal  : (lat, lng) of the dropoff point

        Returns
        -------
        List of [lat, lng] waypoints representing the planned route.
        The first and last points are exact GPS coordinates of start/goal.
        """
        s = _to_cell(*start)
        g = _to_cell(*goal)

        # Trivial case: start and goal are the same cell
        if s == g:
            return [list(start), list(goal)]

        INF = math.inf

        # g_score[v] = best known path cost from start to v
        g_score: dict[tuple[int, int], float] = {s: 0.0}
        # parent[v] = predecessor of v on the best known path
        parent: dict[tuple[int, int], tuple[int, int]] = {s: s}

        # Min-heap: (f_score, cell)
        open_heap: list[tuple[float, tuple[int, int]]] = [
            (0.0 + _euclidean(s, g), s)
        ]

        while open_heap:
            _, cur = heapq.heappop(open_heap)

            if cur == g:
                break

            # --- Lazy Theta*: verify assumed LOS at pop-time ---
            # When cur was pushed, we optimistically assumed line-of-sight
            # from parent[cur] to cur. Verify that now.
            p = parent[cur]
            if p != cur and not _line_of_sight(p, cur, self._blocked):
                # LOS broken: find the best visible grid neighbour to re-parent
                best_g = INF
                for dx, dy in _DIRECTIONS:
                    nb = (cur[0] + dx, cur[1] + dy)
                    if nb in g_score and nb not in self._blocked:
                        cand_g = g_score[nb] + math.sqrt(dx * dx + dy * dy)
                        if cand_g < best_g:
                            best_g = cand_g
                            parent[cur] = nb
                g_score[cur] = best_g

            # --- Expand neighbours ---
            for dx, dy in _DIRECTIONS:
                nb = (cur[0] + dx, cur[1] + dy)
                if (
                    nb[0] < 0 or nb[1] < 0
                    or nb[0] > self.grid_size or nb[1] > self.grid_size
                    or nb in self._blocked
                ):
                    continue

                # Optimistically assume LOS from parent(cur) to nb;
                # this will be verified when nb is popped.
                p = parent[cur]
                tentative_g = g_score[p] + _euclidean(p, nb)

                if tentative_g < g_score.get(nb, INF):
                    g_score[nb] = tentative_g
                    parent[nb] = p
                    f = tentative_g + _euclidean(nb, g)
                    heapq.heappush(open_heap, (f, nb))

        # --- No path found: straight-line fallback ---
        if g not in parent:
            return [list(start), list(goal)]

        # --- Reconstruct path from goal back to start ---
        path_cells: list[tuple[int, int]] = []
        cur = g
        while cur != parent[cur]:
            path_cells.append(cur)
            cur = parent[cur]
        path_cells.append(cur)
        path_cells.reverse()

        waypoints = [_to_coord(c) for c in path_cells]

        # Pin exact GPS coordinates at both ends
        waypoints[0] = list(start)
        waypoints[-1] = list(goal)

        return waypoints


# ---------------------------------------------------------------------------
# Backwards-compatibility alias
# The rest of the codebase instantiates AStarPlanner — keep that name working.
# ---------------------------------------------------------------------------
AStarPlanner = ThetaStarPlanner
