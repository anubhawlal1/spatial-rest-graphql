from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, crud
from .database import SessionLocal, engine, Base
from jose import JWTError, jwt
from datetime import timedelta

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Spatial Data Platform API")

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, crud.SECRET_KEY, algorithms=[crud.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

# --- Exception Handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# --- Auth Endpoints ---
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db, user)
    return db_user

@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = crud.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Points (Protected) ---
@app.post("/points/", response_model=schemas.PointOut)
def create_point(point: schemas.PointCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db_point = crud.create_point(db, point)
    return crud.point_to_schema(db_point)

@app.get("/points/", response_model=List[schemas.PointOut])
def list_points(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    points = crud.get_points(db, skip=skip, limit=limit)
    return [crud.point_to_schema(p) for p in points]

@app.get("/points/{point_id}", response_model=schemas.PointOut)
def get_point(point_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db_point = crud.get_point(db, point_id)
    if not db_point:
        raise HTTPException(status_code=404, detail="Point not found")
    return crud.point_to_schema(db_point)

@app.put("/points/{point_id}", response_model=schemas.PointOut)
def update_point(point_id: int, point: schemas.PointUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db_point = crud.update_point(db, point_id, point)
    if not db_point:
        raise HTTPException(status_code=404, detail="Point not found")
    return crud.point_to_schema(db_point)

@app.delete("/points/{point_id}", response_model=schemas.PointOut)
def delete_point(point_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db_point = crud.delete_point(db, point_id)
    if not db_point:
        raise HTTPException(status_code=404, detail="Point not found")
    return crud.point_to_schema(db_point)

# --- Polygons (Protected) ---
@app.post("/polygons/", response_model=schemas.PolygonOut)
def create_polygon(polygon: schemas.PolygonCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db_polygon = crud.create_polygon(db, polygon)
    return crud.polygon_to_schema(db_polygon)

@app.get("/polygons/", response_model=List[schemas.PolygonOut])
def list_polygons(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    polygons = crud.get_polygons(db, skip=skip, limit=limit)
    return [crud.polygon_to_schema(p) for p in polygons]

@app.get("/polygons/{polygon_id}", response_model=schemas.PolygonOut)
def get_polygon(polygon_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db_polygon = crud.get_polygon(db, polygon_id)
    if not db_polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")
    return crud.polygon_to_schema(db_polygon)

@app.put("/polygons/{polygon_id}", response_model=schemas.PolygonOut)
def update_polygon(polygon_id: int, polygon: schemas.PolygonUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db_polygon = crud.update_polygon(db, polygon_id, polygon)
    if not db_polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")
    return crud.polygon_to_schema(db_polygon)

@app.delete("/polygons/{polygon_id}", response_model=schemas.PolygonOut)
def delete_polygon(polygon_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db_polygon = crud.delete_polygon(db, polygon_id)
    if not db_polygon:
        raise HTTPException(status_code=404, detail="Polygon not found")
    return crud.polygon_to_schema(db_polygon)

# --- Spatial Query Endpoints (Protected) ---
@app.post("/points/within-polygon/", response_model=List[schemas.PointOut])
def points_within_polygon(query: schemas.PointWithinPolygonQuery, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    points = crud.points_within_polygon(db, query.polygon)
    return [crud.point_to_schema(p) for p in points]

@app.post("/polygons/containing-point/", response_model=List[schemas.PolygonOut])
def polygons_containing_point(query: schemas.PolygonContainingPointQuery, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    polygons = crud.polygons_containing_point(db, query.point)
    return [crud.polygon_to_schema(p) for p in polygons]

@app.post("/points/nearby/", response_model=List[schemas.PointOut])
def points_nearby(query: schemas.PointsNearbyQuery, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    points = crud.points_nearby(db, query.point, query.radius)
    return [crud.point_to_schema(p) for p in points] 