from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import text
from app.api import airspace, auth, darkstores, drones, orders, products, simulation
from app.database.session import Base, SessionLocal, engine
from app.ml.battery_model import train_model
from app.services.seed import seed_database
from app.simulation.engine import simulation_engine
from app.websocket.manager import sio, telemetry_manager


app = FastAPI(title="Autonomous Drone Delivery Simulation Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(darkstores.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(drones.router, prefix="/api")
app.include_router(airspace.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            has_postgis = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis')")).scalar()
    except ProgrammingError:
        # Local PostgreSQL often requires a superuser to enable PostGIS.
        # The app can continue once `CREATE EXTENSION postgis` has been run manually.
        has_postgis = False
    if not has_postgis:
        raise RuntimeError(
            "PostGIS is not enabled for database 'drone_delivery'. "
            "Connect as PostgreSQL superuser and run: "
            "CREATE EXTENSION IF NOT EXISTS postgis;"
        )
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    train_model()


@app.on_event("shutdown")
def shutdown() -> None:
    simulation_engine.stop()


@app.get("/api/health")
def health():
    return {"ok": True, "service": "drone-delivery"}


@app.websocket("/ws/telemetry/{order_id}")
async def telemetry_socket(websocket: WebSocket, order_id: str):
    await telemetry_manager.connect(order_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry_manager.disconnect(order_id, websocket)


socket_app = ASGIApp(sio, other_asgi_app=app, socketio_path="/socket.io")
