from sqlalchemy.orm import Session
from . import models, schemas
from shapely.geometry import shape, mapping
from geoalchemy2.shape import from_shape, to_shape
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from datetime import datetime, timedelta
from typing import Optional, List
import os

# --- Helper to convert tuples to lists for GeoJSON ---
def tuple_to_list(obj):
    if isinstance(obj, tuple):
        return list(obj)
    if isinstance(obj, list):
        return [tuple_to_list(i) for i in obj]
    if isinstance(obj, dict):
        return {k: tuple_to_list(v) for k, v in obj.items()}
    return obj

# --- Auth helpers ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already registered")
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# --- Points CRUD ---
def create_point(db: Session, point: schemas.PointCreate):
    try:
        geom = from_shape(shape(point.location), srid=4326)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid GeoJSON for Point")
    db_point = models.SpatialPoint(name=point.name, description=point.description, location=geom)
    db.add(db_point)
    db.commit()
    db.refresh(db_point)
    return db_point

def get_point(db: Session, point_id: int):
    return db.query(models.SpatialPoint).filter(models.SpatialPoint.id == point_id).first()

def get_points(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SpatialPoint).offset(skip).limit(limit).all()

def update_point(db: Session, point_id: int, point: schemas.PointUpdate):
    db_point = get_point(db, point_id)
    if db_point:
        try:
            db_point.name = point.name
            db_point.description = point.description
            db_point.location = from_shape(shape(point.location), srid=4326)
            db.commit()
            db.refresh(db_point)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=422, detail="Invalid GeoJSON for Point")
    return db_point

def delete_point(db: Session, point_id: int):
    db_point = get_point(db, point_id)
    if db_point:
        db.delete(db_point)
        db.commit()
    return db_point

# --- Polygons CRUD ---
def create_polygon(db: Session, polygon: schemas.PolygonCreate):
    try:
        geom = from_shape(shape(polygon.area), srid=4326)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid GeoJSON for Polygon")
    db_polygon = models.SpatialPolygon(name=polygon.name, description=polygon.description, area=geom)
    db.add(db_polygon)
    db.commit()
    db.refresh(db_polygon)
    return db_polygon

def get_polygon(db: Session, polygon_id: int):
    return db.query(models.SpatialPolygon).filter(models.SpatialPolygon.id == polygon_id).first()

def get_polygons(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.SpatialPolygon).offset(skip).limit(limit).all()

def update_polygon(db: Session, polygon_id: int, polygon: schemas.PolygonUpdate):
    db_polygon = get_polygon(db, polygon_id)
    if db_polygon:
        try:
            db_polygon.name = polygon.name
            db_polygon.description = polygon.description
            db_polygon.area = from_shape(shape(polygon.area), srid=4326)
            db.commit()
            db.refresh(db_polygon)
        except Exception:
            db.rollback()
            raise HTTPException(status_code=422, detail="Invalid GeoJSON for Polygon")
    return db_polygon

def delete_polygon(db: Session, polygon_id: int):
    db_polygon = get_polygon(db, polygon_id)
    if db_polygon:
        db.delete(db_polygon)
        db.commit()
    return db_polygon

def point_to_schema(db_point: models.SpatialPoint):
    geojson = mapping(to_shape(db_point.location))
    geojson = tuple_to_list(geojson)
    return schemas.PointOut(
        id=db_point.id,
        name=db_point.name,
        description=db_point.description,
        location=geojson
    )

def polygon_to_schema(db_polygon: models.SpatialPolygon):
    geojson = mapping(to_shape(db_polygon.area))
    geojson = tuple_to_list(geojson)
    return schemas.PolygonOut(
        id=db_polygon.id,
        name=db_polygon.name,
        description=db_polygon.description,
        area=geojson
    )

# --- Spatial Queries ---
def points_within_polygon(db: Session, polygon_geojson: dict) -> List[models.SpatialPoint]:
    try:
        poly_shape = from_shape(shape(polygon_geojson), srid=4326)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid GeoJSON for Polygon")
    return db.query(models.SpatialPoint).filter(models.SpatialPoint.location.ST_Within(poly_shape)).all()

def polygons_containing_point(db: Session, point_geojson: dict) -> List[models.SpatialPolygon]:
    try:
        pt_shape = from_shape(shape(point_geojson), srid=4326)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid GeoJSON for Point")
    return db.query(models.SpatialPolygon).filter(models.SpatialPolygon.area.ST_Contains(pt_shape)).all()

def points_nearby(db: Session, point_geojson: dict, radius: float) -> List[models.SpatialPoint]:
    try:
        pt_shape = from_shape(shape(point_geojson), srid=4326)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid GeoJSON for Point")
    # radius in meters, geography cast for accurate distance
    return db.query(models.SpatialPoint).filter(models.SpatialPoint.location.ST_DWithin(pt_shape, radius)).all() 