# main.py
# FINAL WORKING VERSION – FULLY FIXED

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Any, Optional
import pandas as pd
import joblib
from datetime import datetime

import models, crud, hashing
from database import SessionLocal, engine
from services import weather, routing

# Create tables
models.Base.metadata.create_all(bind=engine)

# Load AI Model
ai_model = joblib.load("congestion_model.pkl")

app = FastAPI(title="Traffix Backend API")

# ----------------- Pydantic Models -----------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    email: EmailStr
    class Config: from_attributes = True

class ReportCreate(BaseModel):
    report_type: str
    lat: float
    lon: float

class ReportResponse(BaseModel):
    id: int
    report_type: str
    lat: float
    lon: float
    class Config: from_attributes = True

class FloodHotspotResponse(BaseModel):
    id: int
    description: str
    lat: float
    lon: float
    class Config: from_attributes = True

class RouteRequest(BaseModel):
    start_address: str
    end_address: str

class RouteData(BaseModel):
    risk_score: int
    reason: str
    distance_km: float
    duration_min: float
    geometry: Any

class RouteResponse(BaseModel):
    original_route: RouteData
    alternative_route: Optional[RouteData] = None


# ----------------- DB Dependency -----------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Traffix backend running!"}


# ----------------- USER AUTH -----------------

@app.post("/users/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, email=user.email, password=user.password)


@app.post("/users/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, user.email)
    if not db_user or not hashing.Hash.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=404, detail="Invalid email or password")
    return {"message": "Login success", "token": db_user.id}


# ----------------- HAZARD REPORTING -----------------

@app.post("/report/fast", response_model=ReportResponse)
def create_report(report: ReportCreate, user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new = crud.create_new_report(
        db=db,
        report_type=report.report_type,
        lat=report.lat,
        lon=report.lon,
        user_id=user_id,
        city_id=1
    )

    return ReportResponse(
        id=new.id,
        report_type=new.report_type,
        lat=report.lat,
        lon=report.lon
    )


# ----------------- FIXED /hazards/live -----------------

@app.get("/hazards/live", response_model=List[ReportResponse])
def get_live_hazards(db: Session = Depends(get_db)):
    reports = crud.get_live_reports(db, city_id=1)
    response_list = []

    for rep in reports:
        try:
            lat = db.query(func.ST_Y(func.ST_AsText(rep.location))).scalar()
            lon = db.query(func.ST_X(func.ST_AsText(rep.location))).scalar()

            if lat is None or lon is None:
                continue

            response_list.append(
                ReportResponse(
                    id=rep.id,
                    report_type=rep.report_type,
                    lat=lat,
                    lon=lon
                )
            )
        except Exception as e:
            print("Error converting hazard:", e)
            continue

    return response_list


# ----------------- STATIC HAZARDS -----------------

@app.get("/hazards/static", response_model=List[FloodHotspotResponse])
def get_static_hazards(db: Session = Depends(get_db)):
    spots = crud.get_static_hazards(db, city_id=1)
    out = []

    for s in spots:
        lat = db.query(func.ST_Y(func.ST_AsText(s.location))).scalar()
        lon = db.query(func.ST_X(func.ST_AsText(s.location))).scalar()
        out.append(FloodHotspotResponse(
            id=s.id,
            description=s.description,
            lat=lat,
            lon=lon
        ))

    return out


# ----------------- ROUTE + AI RISK -----------------

@app.post("/route/predict-risk", response_model=RouteResponse)
def predict_route_risk(req: RouteRequest, db: Session = Depends(get_db)):

    start = routing.get_coords_from_address(req.start_address)
    end = routing.get_coords_from_address(req.end_address)

    if not start:
        raise HTTPException(404, f"Location not found: {req.start_address}")
    if not end:
        raise HTTPException(404, f"Location not found: {req.end_address}")

    routes = routing.get_routes_from_osrm(start['lat'], start['lon'], end['lat'], end['lon'])
    if not routes:
        raise HTTPException(404, "No route found")

    original = routes[0]["geometry"]

    report_count = crud.get_reports_near_route(db, original, city_id=1)
    w = weather.get_current_weather(start["lat"], start["lon"])
    static_score = crud.get_sample_road_score(db, city_id=1)
    hour = datetime.now().hour

    df = pd.DataFrame({
        "static_hazard_score": [static_score],
        "active_reports": [report_count],
        "is_raining": [1 if w["is_raining"] else 0],
        "hour_of_day": [hour]
    })

    prediction = ai_model.predict(df)[0]
    high_risk = (prediction == 1) or (report_count > 0)

    reason = "Risk: Low. Route looks clear."
    if high_risk:
        reason = f"Risk: High. {report_count} report(s). Weather temp {w['temp']}°C"

    orig = routes[0]
    orig_data = RouteData(
        risk_score=1 if high_risk else 0,
        reason=reason,
        distance_km=round(orig["distance"] / 1000, 1),
        duration_min=round(orig["duration"] / 60, 0),
        geometry=orig["geometry"]
    )

    alt_data = None
    if len(routes) > 1:
        alt = routes[1]
        alt_data = RouteData(
            risk_score=0,
            reason="Alternative route",
            distance_km=round(alt["distance"] / 1000, 1),
            duration_min=round(alt["duration"] / 60, 0),
            geometry=alt["geometry"]
        )

    if high_risk and alt_data:
        return RouteResponse(original_route=alt_data, alternative_route=orig_data)

    return RouteResponse(original_route=orig_data, alternative_route=alt_data)
