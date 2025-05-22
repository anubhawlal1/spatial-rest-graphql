import strawberry
from typing import List, Optional, Any
from strawberry.types import Info
from . import crud, models, database
from sqlalchemy.orm import Session
import json
import typing as t

# --- Custom JSON Scalar ---
@strawberry.scalar(description="The `JSON` scalar type represents arbitrary JSON data.")
class JSON:
    @staticmethod
    def serialize(value: t.Any) -> str:
        return json.dumps(value)
    @staticmethod
    def parse_value(value: str) -> t.Any:
        return json.loads(value)

# --- Strawberry Types ---
@strawberry.type
class Point:
    id: int
    name: str
    description: Optional[str]
    location: JSON

@strawberry.type
class Polygon:
    id: int
    name: str
    description: Optional[str]
    area: JSON

@strawberry.type
class User:
    id: int
    username: str

@strawberry.type
class Token:
    access_token: str
    token_type: str

# --- Auth Helper ---
def get_db() -> Session:
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(info: Info) -> Optional[User]:
    request = info.context["request"]
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        from jose import jwt
        payload = jwt.decode(token, crud.SECRET_KEY, algorithms=[crud.ALGORITHM])
        username = payload.get("sub")
        if not username:
            return None
        db = next(get_db())
        user = crud.get_user_by_username(db, username)
        if user:
            return User(id=user.id, username=user.username)
    except Exception:
        return None
    return None

# --- Queries ---
@strawberry.type
class Query:
    @strawberry.field
    def points(self, info: Info) -> List[Point]:
        db = next(get_db())
        return [Point(**crud.point_to_dict(p)) for p in crud.get_points(db)]

    @strawberry.field
    def polygons(self, info: Info) -> List[Polygon]:
        db = next(get_db())
        return [Polygon(**crud.polygon_to_dict(p)) for p in crud.get_polygons(db)]

    @strawberry.field
    def point(self, info: Info, id: int) -> Optional[Point]:
        db = next(get_db())
        p = crud.get_point(db, id)
        return Point(**crud.point_to_dict(p)) if p else None

    @strawberry.field
    def polygon(self, info: Info, id: int) -> Optional[Polygon]:
        db = next(get_db())
        p = crud.get_polygon(db, id)
        return Polygon(**crud.polygon_to_dict(p)) if p else None

    @strawberry.field
    def points_within_polygon(self, info: Info, polygon: str) -> List[Point]:
        db = next(get_db())
        poly_geojson = json.loads(polygon)
        return [Point(**crud.point_to_dict(p)) for p in crud.points_within_polygon(db, poly_geojson)]

    @strawberry.field
    def polygons_containing_point(self, info: Info, point: str) -> List[Polygon]:
        db = next(get_db())
        pt_geojson = json.loads(point)
        return [Polygon(**crud.polygon_to_dict(p)) for p in crud.polygons_containing_point(db, pt_geojson)]

    @strawberry.field
    def points_nearby(self, info: Info, point: str, radius: float) -> List[Point]:
        db = next(get_db())
        pt_geojson = json.loads(point)
        return [Point(**crud.point_to_dict(p)) for p in crud.points_nearby(db, pt_geojson, radius)]

# --- Mutations ---
@strawberry.type
class Mutation:
    @strawberry.mutation
    def register(self, info: Info, username: str, password: str) -> bool:
        db = next(get_db())
        user = crud.create_user(db, username, password)
        return user is not None

    @strawberry.mutation
    def login(self, info: Info, username: str, password: str) -> Optional[Token]:
        db = next(get_db())
        user = crud.authenticate_user(db, username, password)
        if not user:
            return None
        access_token = crud.create_access_token({"sub": user.username})
        return Token(access_token=access_token, token_type="bearer")

    @strawberry.mutation
    def create_point(self, info: Info, name: str, description: str, location: str) -> Optional[Point]:
        db = next(get_db())
        loc_geojson = json.loads(location)
        p = crud.create_point(db, name, description, loc_geojson)
        return Point(**crud.point_to_dict(p)) if p else None

    @strawberry.mutation
    def update_point(self, info: Info, id: int, name: str, description: str, location: str) -> Optional[Point]:
        db = next(get_db())
        loc_geojson = json.loads(location)
        p = crud.update_point(db, id, name, description, loc_geojson)
        return Point(**crud.point_to_dict(p)) if p else None

    @strawberry.mutation
    def delete_point(self, info: Info, id: int) -> bool:
        db = next(get_db())
        return crud.delete_point(db, id)

    @strawberry.mutation
    def create_polygon(self, info: Info, name: str, description: str, area: str) -> Optional[Polygon]:
        db = next(get_db())
        area_geojson = json.loads(area)
        p = crud.create_polygon(db, name, description, area_geojson)
        return Polygon(**crud.polygon_to_dict(p)) if p else None

    @strawberry.mutation
    def update_polygon(self, info: Info, id: int, name: str, description: str, area: str) -> Optional[Polygon]:
        db = next(get_db())
        area_geojson = json.loads(area)
        p = crud.update_polygon(db, id, name, description, area_geojson)
        return Polygon(**crud.polygon_to_dict(p)) if p else None

    @strawberry.mutation
    def delete_polygon(self, info: Info, id: int) -> bool:
        db = next(get_db())
        return crud.delete_polygon(db, id)

schema = strawberry.Schema(query=Query, mutation=Mutation) 