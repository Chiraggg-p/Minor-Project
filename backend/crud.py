# crud.py
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import json

import models
import hashing

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, password: str):
    hashed_password = hashing.Hash.get_password_hash(password)
    new_user = models.User(
        email=email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def create_new_report(db: Session, report_type: str, lat: float, lon: float, user_id: int, city_id: int):
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    new_report = models.Report(
        user_id=user_id,
        city_id=city_id,
        location=point,
        report_type=report_type,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

def get_live_reports(db: Session, city_id: int):
    now = datetime.utcnow()
    return db.query(models.Report).filter(
        models.Report.city_id == city_id,
        models.Report.expires_at > now
    ).all()

def get_static_hazards(db: Session, city_id: int):
    return db.query(models.FloodHotspot).filter(models.FloodHotspot.city_id == city_id).all()

def get_sample_road_score(db: Session, city_id: int):
    seg = db.query(models.RoadSegment).filter(
        models.RoadSegment.city_id == city_id,
        models.RoadSegment.id == 1
    ).first()
    return seg.static_hazard_score if seg else 5

def get_reports_near_route(db: Session, route_geometry: dict, city_id: int):
    """
    Finds count of reports within 300 meters of the given route.
    Uses GEOGRAPHY-based ST_DWithin (correct for meters).
    """
    if not route_geometry:
        return 0

    route_json = json.dumps(route_geometry)
    # Convert GeoJSON to PostGIS geometry and set SRID
    route_line = func.ST_SetSRID(func.ST_GeomFromGeoJSON(route_json), 4326)

    now = datetime.utcnow()
    count_query = db.query(models.Report).filter(
        models.Report.city_id == city_id,
        models.Report.expires_at > now,
        func.ST_DWithin(
            models.Report.location,
            route_line,
            300
        )
    )
    return count_query.count()
