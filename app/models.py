from sqlalchemy import Column, Integer, String, Index
from geoalchemy2 import Geometry
from .database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class SpatialPoint(Base):
    __tablename__ = 'points'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    __table_args__ = (
        Index('idx_points_location', 'location', postgresql_using='gist'),
    )

class SpatialPolygon(Base):
    __tablename__ = 'polygons'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    area = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=False)
    __table_args__ = (
        Index('idx_polygons_area', 'area', postgresql_using='gist'),
    ) 