from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any

# --- Auth Schemas ---
class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Point & Polygon Schemas ---
class PointBase(BaseModel):
    name: str
    description: Optional[str] = None
    location: Dict[str, Any] = Field(..., example={"type": "Point", "coordinates": [77.0365, 38.8977]})

    @validator('location')
    def validate_point(cls, v):
        if v.get('type') != 'Point' or not isinstance(v.get('coordinates'), list):
            raise ValueError('location must be a GeoJSON Point')
        return v

class PointCreate(PointBase):
    pass

class PointUpdate(PointBase):
    pass

class PointOut(PointBase):
    id: int
    class Config:
        orm_mode = True

class PolygonBase(BaseModel):
    name: str
    description: Optional[str] = None
    area: Dict[str, Any] = Field(..., example={"type": "Polygon", "coordinates": [[[77.0, 38.9], [77.1, 38.9], [77.1, 39.0], [77.0, 39.0], [77.0, 38.9]]]})

    @validator('area')
    def validate_polygon(cls, v):
        if v.get('type') != 'Polygon' or not isinstance(v.get('coordinates'), list):
            raise ValueError('area must be a GeoJSON Polygon')
        return v

class PolygonCreate(PolygonBase):
    pass

class PolygonUpdate(PolygonBase):
    pass

class PolygonOut(PolygonBase):
    id: int
    class Config:
        orm_mode = True

# --- Spatial Query Schemas ---
class PointWithinPolygonQuery(BaseModel):
    polygon: Dict[str, Any] = Field(..., example={"type": "Polygon", "coordinates": [[[77.0, 38.9], [77.1, 38.9], [77.1, 39.0], [77.0, 39.0], [77.0, 38.9]]]})

class PolygonContainingPointQuery(BaseModel):
    point: Dict[str, Any] = Field(..., example={"type": "Point", "coordinates": [77.0365, 38.8977]})

class PointsNearbyQuery(BaseModel):
    point: Dict[str, Any] = Field(..., example={"type": "Point", "coordinates": [77.0365, 38.8977]})
    radius: float = Field(..., description="Radius in meters") 