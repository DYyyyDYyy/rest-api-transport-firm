# Transport Firm REST API

REST API for managing the operations of a freight carrier: clients, orders, drivers, vehicles, trip planning and driver trip logs.

**Stack:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, pytest.

## Data model

```
Client 1 ──< Order 1 ── 1 TripDetails >── 1 Vehicle
                            │  └──< TripLog >── 1 Driver
                            └──< trip_drivers >──< Driver
```

| Relationship | Type | Notes |
|---|---|---|
| Client → Order | 1:M | a client cannot be deleted while it has orders |
| Order → TripDetails | 1:1 | deleting an order removes its trip and logs |
| Vehicle → TripDetails | 1:M | |
| TripDetails ↔ Driver | N:M | association table `trip_drivers`; a trip can have several drivers |
| TripDetails → TripLog | 1:M | actual start/end times and driver comments |
| Driver → TripLog | 1:M | a log can only be written by a driver assigned to the trip |

Business rules enforced by the API: cargo weight must fit the vehicle capacity, an unavailable vehicle cannot be assigned, a trip has a single order, and period and positive-value constraints are also guarded by `CHECK` constraints in the database.

## Endpoints

Full CRUD (`GET` list/one, `POST`, `PATCH`, `DELETE`) is available for `/clients`, `/drivers`, `/vehicles`, `/orders`, `/trips` and `/trip-logs`. Interactive docs are served at `/docs`.

Additional queries:

| Endpoint | Description |
|---|---|
| `GET /drivers/{id}/trips` | trip history of a driver with the driver's own log entries |
| `GET /orders/period?date_from=&date_to=` | orders created within the date range (UTC, inclusive) |
| `GET /vehicles/available` | vehicles flagged available and not currently on an in-progress order |

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
docker compose up -d db

alembic upgrade head
python -m scripts.seed        # optional demo data
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs. A Postman collection with example requests and responses is in `docs/postman_collection.json`.

## Migrations

Schema changes go through Alembic:

- `0001` creates the initial schema
- `0002` adds `vehicles.fuel_type`

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

## Tests

```bash
pytest
```

Tests run against the database from `TEST_DATABASE_URL` and recreate its tables for every test.
