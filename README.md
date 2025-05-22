# Spatial Data Platform Backend

This is a FastAPI backend for storing, updating, and retrieving spatial point and polygon data using PostgreSQL + PostGIS.

## Features
- Store, update, and retrieve multiple points (with GeoJSON geometry)
- Store, update, and retrieve multiple polygons (with GeoJSON geometry)
- RESTful API
- GraphQL API (Strawberry)
- JWT Authentication (register/login)
- Spatial queries: points within polygon, polygons containing point, points nearby

## Requirements
- Python 3.8+
- PostgreSQL with PostGIS extension

## Setup

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Set up PostgreSQL with PostGIS
- Install PostgreSQL and PostGIS
  brew install postgresql
  brew install postgis
- Start Postgres
  brew services start postgresql
  
- Create a database and enable PostGIS:

```
psql -U postgres
CREATE DATABASE spatialdb;
\c spatialdb
CREATE EXTENSION postgis;
CREATE ROLE postgres WITH SUPERUSER LOGIN;
```

### 3. Configure environment variables (optional)
- `POSTGRES_USER` (default: postgres)
- `POSTGRES_PASSWORD` (default: postgres)
- `POSTGRES_DB` (default: spatialdb)
- `POSTGRES_HOST` (default: localhost)
- `POSTGRES_PORT` (default: 5432)

### 4. Run the REST API
```
uvicorn app.main:app --reload
```

### 5. Run the GraphQL API
```
uvicorn graphql_app.main:app --reload
```

## REST API Usage

(See previous sections for REST endpoints and curl examples)

---

## GraphQL API Usage

The GraphQL endpoint is available at: `http://localhost:8000/graphql`

You can use the GraphQL Playground in your browser, or use curl as shown below.

### Example curl commands

#### Register a user
```sh
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { register(username: \"alice\", password: \"wonderland\") }"}'
```

#### Login and get JWT token
```sh
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { login(username: \"alice\", password: \"wonderland\") { access_token token_type } }"}'
```

#### Create a point (requires JWT)
```sh
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"query": "mutation { create_point(name: \"White House\", description: \"Famous building\", location: \"{\\\"type\\\": \\\"Point\\\", \\\"coordinates\\\": [77.0365, 38.8977]}\") { id name location } }"}'
```

#### Get all points (requires JWT)
```sh
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"query": "query { points { id name description location } }"}'
```

#### Spatial query: points within polygon (requires JWT)
```sh
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"query": "query { points_within_polygon(polygon: \"{\\\"type\\\": \\\"Polygon\\\", \\\"coordinates\\\": [[[77.0, 38.9], [77.1, 38.9], [77.1, 39.0], [77.0, 39.0], [77.0, 38.9]]]}\") { id name location } }"}'
```

Replace `<TOKEN>` with the JWT you get from the login mutation.

---

You can test the REST API at `http://localhost:8000/docs` and the GraphQL API at `http://localhost:8000/graphql` after running the respective servers.
# spatial-rest-graphql
