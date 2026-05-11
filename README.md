# Autonomous Drone Delivery Simulation Platform

Production-style full-stack simulation for autonomous drone grocery and package delivery in Hyderabad, India.

## Stack

- Frontend: HTML, CSS, Vanilla JavaScript, Leaflet.js, Socket.IO client
- Backend: Python FastAPI, SQLAlchemy, WebSockets, Socket.IO ASGI
- Database: PostgreSQL with PostGIS
- Optimization: A* route planning and Google OR-Tools drone assignment
- ML: scikit-learn Random Forest battery usage prediction saved with joblib
- Local runtime: FastAPI backend, static frontend server, PostgreSQL/PostGIS, optional Redis

## Local Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a local PostgreSQL database with PostGIS:

```sql
CREATE USER drone WITH PASSWORD 'drone';
CREATE DATABASE drone_delivery OWNER drone;
\c drone_delivery
CREATE EXTENSION IF NOT EXISTS postgis;
```

Copy local environment settings:

```bash
copy backend\.env.example backend\.env
```

Start the backend:

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

Start the frontend from another terminal:

```bash
cd frontend
python -m http.server 8080
```

Open:

- Frontend: http://localhost:8080/pages/login.html
- Backend API docs: http://localhost:8000/docs

Redis is optional for local development. If Redis is not running, weather data falls back to synthetic uncached values.

Seeded accounts:

- Admin: `admin@hyd-drone.local` / `admin123`
- Customer: `customer@hyd-drone.local` / `customer123`

## Hyderabad Scope

All seeded hubs, drone fleets, routes, orders, and restrictions are constrained to Hyderabad coordinates.

Seeded dark stores:

- Gachibowli
- Madhapur
- Kukatpally
- Secunderabad
- LB Nagar
- Uppal

Seeded no-fly zones include airport and military-style restrictions around Hyderabad.

## Main Features

- JWT signup/login/logout with bcrypt password hashing
- Role-based customer and admin pages
- Grocery ordering with cart and nearest stocked dark store assignment
- Package delivery with map-selected pickup and destination
- Drone assignment with OR-Tools
- Grid A* route generation avoiding restricted polygons
- PostGIS geometry columns for points, lines, and polygons
- Real-time telemetry through WebSockets and Socket.IO
- Simulation control with configurable failure probability and telemetry interval
- Random Forest battery prediction using synthetic weather, distance, and payload data
- Redis weather cache with optional OpenWeatherMap integration
- Admin analytics with per-hub metrics and live operations map

## API Highlights

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/orders/create`
- `GET /api/orders/list`
- `GET /api/orders/status/{order_id}`
- `GET /api/drones`
- `POST /api/drones/add`
- `PUT /api/drones/update/{drone_id}`
- `DELETE /api/drones/delete/{drone_id}`
- `POST /api/zones/create`
- `GET /api/zones/list`
- `POST /api/simulation/start`
- `POST /api/simulation/stop`
- `WS /ws/telemetry/{order_id}`
- Socket.IO path: `/socket.io`

## Notes

The simulation is intentionally modular: services can be swapped for more sophisticated airspace validation, weather providers, route smoothing, dispatch rules, or a dedicated background worker without changing the static frontend contract.
