from geoalchemy2.functions import ST_GeomFromText
from sqlalchemy.orm import Session
from app.models import AirspaceZone, DarkStore, Drone, Product, SimulationConfig, User
from app.utils.geo import point_wkt, polygon_wkt
from app.utils.security import hash_password


DARK_STORES = [
    ("Gachibowli Hub", 17.4401, 78.3489, "Gachibowli, Hyderabad", 5200, 14, 4800),
    ("Madhapur Hub", 17.4483, 78.3915, "Madhapur, Hyderabad", 4600, 12, 4100),
    ("Kukatpally Hub", 17.4948, 78.3996, "Kukatpally, Hyderabad", 4300, 10, 3900),
    ("Secunderabad Hub", 17.4399, 78.4983, "Secunderabad, Hyderabad", 5000, 13, 4550),
    ("LB Nagar Hub", 17.3457, 78.5522, "LB Nagar, Hyderabad", 3900, 9, 3600),
    ("Uppal Hub", 17.4058, 78.5591, "Uppal, Hyderabad", 4100, 10, 3750),
]


PRODUCTS = [
    ("Fresh Milk", "Dairy", 68, 1.0),
    ("Greek Yogurt", "Dairy", 95, 0.5),
    ("Cheese Slices", "Dairy", 140, 0.3),
    ("Bananas", "Produce", 55, 1.2),
    ("Tomatoes", "Produce", 42, 1.0),
    ("Potatoes", "Produce", 38, 1.0),
    ("Onions", "Produce", 36, 1.0),
    ("Coriander Bunch", "Produce", 18, 0.1),
    ("Basmati Rice", "Staples", 210, 2.0),
    ("Toor Dal", "Staples", 165, 1.0),
    ("Atta", "Staples", 235, 5.0),
    ("Sunflower Oil", "Staples", 155, 1.0),
    ("Bread", "Bakery", 45, 0.4),
    ("Brown Bread", "Bakery", 60, 0.45),
    ("Croissant Pack", "Bakery", 120, 0.35),
    ("Eggs Pack", "Dairy", 92, 0.7),
    ("Instant Coffee", "Pantry", 180, 0.2),
    ("Tea Powder", "Pantry", 145, 0.25),
    ("Peanut Butter", "Pantry", 220, 0.5),
    ("Cornflakes", "Breakfast", 185, 0.6),
    ("Oats", "Breakfast", 150, 1.0),
    ("Apples", "Produce", 160, 1.0),
    ("Paneer", "Dairy", 120, 0.5),
    ("Dark Chocolate", "Snacks", 110, 0.1),
    ("Potato Chips", "Snacks", 40, 0.08),
    ("Cookies", "Snacks", 75, 0.2),
    ("Orange Juice", "Beverages", 115, 1.0),
    ("Mineral Water", "Beverages", 30, 1.0),
    ("Energy Drink", "Beverages", 95, 0.3),
    ("Toothpaste", "Personal Care", 85, 0.15),
    ("Shampoo", "Personal Care", 190, 0.35),
    ("Dishwash Liquid", "Home Care", 125, 0.7),
    ("Laundry Detergent", "Home Care", 260, 1.0),
]


ZONES = [
    ("Rajiv Gandhi Airport Restriction", "airport", [[17.224, 78.407], [17.266, 78.407], [17.266, 78.468], [17.224, 78.468]]),
    ("Hakimpet Air Force Restriction", "military", [[17.536, 78.515], [17.568, 78.515], [17.568, 78.555], [17.536, 78.555]]),
    ("Bolarum Cantonment Restriction", "military", [[17.492, 78.500], [17.525, 78.500], [17.525, 78.535], [17.492, 78.535]]),
]


def seed_database(db: Session) -> None:
    if not db.query(User).filter(User.email == "admin@hyd-drone.local").first():
        db.add(User(name="Admin", email="admin@hyd-drone.local", role="admin", hashed_password=hash_password("admin123")))
        db.add(User(name="Customer", email="customer@hyd-drone.local", role="customer", hashed_password=hash_password("customer123")))

    if db.query(DarkStore).count() == 0:
        stores = []
        for name, lat, lng, address, capacity, slots, stock in DARK_STORES:
            store = DarkStore(
                name=name,
                latitude=lat,
                longitude=lng,
                address=address,
                inventory_capacity=capacity,
                charging_slots=slots,
                available_stock=stock,
                location=ST_GeomFromText(point_wkt(lat, lng), 4326),
            )
            db.add(store)
            stores.append(store)
        db.flush()
        for store in stores:
            for n in range(4):
                db.add(Drone(
                    model=f"AeroSwift-{store.id}{n}",
                    max_payload=5.0 + n * 0.5,
                    max_range=38,
                    battery_capacity=100,
                    current_battery=92 - n * 4,
                    latitude=store.latitude,
                    longitude=store.longitude,
                    status="idle",
                    dark_store_id=store.id,
                    location=ST_GeomFromText(point_wkt(store.latitude, store.longitude), 4326),
                ))
            _ensure_products_for_store(db, store.id)
    else:
        for store in db.query(DarkStore).all():
            _ensure_products_for_store(db, store.id)

    if db.query(AirspaceZone).count() == 0:
        for name, zone_type, coords in ZONES:
            db.add(AirspaceZone(name=name, zone_type=zone_type, coordinates=coords, polygon=ST_GeomFromText(polygon_wkt(coords), 4326)))

    if db.query(SimulationConfig).count() == 0:
        db.add(SimulationConfig(running=False, failure_probability=0.05, telemetry_interval=2, max_orders=30))
    db.commit()


def _ensure_products_for_store(db: Session, store_id: int) -> None:
    existing = {
        p.name
        for p in db.query(Product).filter(Product.dark_store_id == store_id).all()
    }
    for name, category, price, weight in PRODUCTS:
        if name not in existing:
            db.add(Product(name=name, category=category, price=price, weight_kg=weight, stock=240, dark_store_id=store_id))
