from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.functions import ST_GeomFromText
from sqlalchemy.orm import Session
from app.api.deps import require_admin
from app.database.session import get_db
from app.models import AirspaceZone
from app.schemas.common import ZoneCreate
from app.utils.geo import polygon_wkt


router = APIRouter(prefix="/zones", tags=["airspace"])


@router.get("/list")
def list_zones(db: Session = Depends(get_db)):
    return [_zone(z) for z in db.query(AirspaceZone).order_by(AirspaceZone.id).all()]


@router.post("/create")
def create_zone(payload: ZoneCreate, _=Depends(require_admin), db: Session = Depends(get_db)):
    zone = AirspaceZone(name=payload.name, zone_type=payload.zone_type, coordinates=payload.coordinates, polygon=ST_GeomFromText(polygon_wkt(payload.coordinates), 4326))
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return _zone(zone)


@router.put("/{zone_id}")
def update_zone(zone_id: int, payload: ZoneCreate, _=Depends(require_admin), db: Session = Depends(get_db)):
    zone = db.query(AirspaceZone).filter(AirspaceZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    zone.name = payload.name
    zone.zone_type = payload.zone_type
    zone.coordinates = payload.coordinates
    zone.polygon = ST_GeomFromText(polygon_wkt(payload.coordinates), 4326)
    db.commit()
    return _zone(zone)


@router.delete("/{zone_id}")
def delete_zone(zone_id: int, _=Depends(require_admin), db: Session = Depends(get_db)):
    zone = db.query(AirspaceZone).filter(AirspaceZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(zone)
    db.commit()
    return {"ok": True}


def _zone(z: AirspaceZone) -> dict:
    return {"id": z.id, "name": z.name, "zone_type": z.zone_type, "coordinates": z.coordinates, "active": z.active}
