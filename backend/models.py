# models.py
from sqlalchemy import Column, Integer, String, SmallInteger, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from sqlalchemy.sql import func
from database import Base

class City(Base):
    __tablename__ = "cities"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    country = Column(String(100))

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RoadSegment(Base):
    __tablename__ = "road_segments"
    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"))
    path = Column(Geography(geometry_type='LINESTRING', srid=4326))
    static_hazard_score = Column(SmallInteger, default=0)

class FloodHotspot(Base):
    __tablename__ = "flood_hotspots"
    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.id"))
    location = Column(Geography(geometry_type='POINT', srid=4326))
    description = Column(Text)

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    city_id = Column(Integer, ForeignKey("cities.id"))
    location = Column(Geography(geometry_type='POINT', srid=4326))
    report_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
