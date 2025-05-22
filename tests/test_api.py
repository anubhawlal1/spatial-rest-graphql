import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

USERNAME = "apitestuser"
PASSWORD = "apitestpass"

@pytest.fixture(scope="module")
def auth_headers():
    # Register
    client.post("/register", json={"username": USERNAME, "password": PASSWORD})
    # Login
    r = client.post("/token", data={"username": USERNAME, "password": PASSWORD})
    assert r.status_code == 200
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_auth_required():
    # Should fail without token
    r = client.get("/points/")
    assert r.status_code == 401

def test_point_crud(auth_headers):
    # Create point
    point = {
        "name": "API Test Point",
        "description": "A test point",
        "location": {"type": "Point", "coordinates": [77.0365, 38.8977]}
    }
    r = client.post("/points/", json=point, headers=auth_headers)
    assert r.status_code == 200
    point_id = r.json()["id"]

    # Get point
    r = client.get(f"/points/{point_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == point["name"]

    # Update point
    updated = point.copy()
    updated["name"] = "Updated Point"
    r = client.put(f"/points/{point_id}", json=updated, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Point"

    # List points
    r = client.get("/points/", headers=auth_headers)
    assert r.status_code == 200
    assert any(p["id"] == point_id for p in r.json())

    # Delete point
    r = client.delete(f"/points/{point_id}", headers=auth_headers)
    assert r.status_code == 200
    # Should not find after delete
    r = client.get(f"/points/{point_id}", headers=auth_headers)
    assert r.status_code == 404

def test_polygon_crud(auth_headers):
    # Create polygon
    polygon = {
        "name": "API Test Polygon",
        "description": "A test polygon",
        "area": {"type": "Polygon", "coordinates": [[[77.0, 38.9], [77.1, 38.9], [77.1, 39.0], [77.0, 39.0], [77.0, 38.9]]]}
    }
    r = client.post("/polygons/", json=polygon, headers=auth_headers)
    assert r.status_code == 200
    polygon_id = r.json()["id"]

    # Get polygon
    r = client.get(f"/polygons/{polygon_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == polygon["name"]

    # Update polygon
    updated = polygon.copy()
    updated["name"] = "Updated Polygon"
    r = client.put(f"/polygons/{polygon_id}", json=updated, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Polygon"

    # List polygons
    r = client.get("/polygons/", headers=auth_headers)
    assert r.status_code == 200
    assert any(p["id"] == polygon_id for p in r.json())

    # Delete polygon
    r = client.delete(f"/polygons/{polygon_id}", headers=auth_headers)
    assert r.status_code == 200
    # Should not find after delete
    r = client.get(f"/polygons/{polygon_id}", headers=auth_headers)
    assert r.status_code == 404

def test_spatial_queries(auth_headers):
    # Create a polygon and a point inside it
    polygon = {
        "name": "Spatial Query Polygon",
        "description": "Polygon for spatial query",
        "area": {"type": "Polygon", "coordinates": [[[77.0, 38.9], [77.1, 38.9], [77.1, 39.0], [77.0, 39.0], [77.0, 38.9]]]}
    }
    r = client.post("/polygons/", json=polygon, headers=auth_headers)
    assert r.status_code == 200
    polygon_id = r.json()["id"]

    point = {
        "name": "Spatial Query Point",
        "description": "Point for spatial query",
        "location": {"type": "Point", "coordinates": [77.05, 38.95]}
    }
    r = client.post("/points/", json=point, headers=auth_headers)
    assert r.status_code == 200
    point_id = r.json()["id"]

    # Points within polygon
    query = {"polygon": polygon["area"]}
    r = client.post("/points/within-polygon/", json=query, headers=auth_headers)
    assert r.status_code == 200
    assert any(p["id"] == point_id for p in r.json())

    # Polygons containing point
    query = {"point": point["location"]}
    r = client.post("/polygons/containing-point/", json=query, headers=auth_headers)
    assert r.status_code == 200
    assert any(p["id"] == polygon_id for p in r.json())

    # Points nearby (within 10000 meters)
    query = {"point": point["location"], "radius": 10000}
    r = client.post("/points/nearby/", json=query, headers=auth_headers)
    assert r.status_code == 200
    assert any(p["id"] == point_id for p in r.json()) 