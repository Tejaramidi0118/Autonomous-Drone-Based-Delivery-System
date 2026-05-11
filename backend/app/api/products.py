from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import Product


router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [
        {"id": p.id, "name": p.name, "category": p.category, "price": p.price, "weight_kg": p.weight_kg, "stock": p.stock, "dark_store_id": p.dark_store_id}
        for p in products
    ]
