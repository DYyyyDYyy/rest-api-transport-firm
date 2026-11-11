# Transport Firm REST API

[![ci](https://github.com/DYyyyDYyy/rest-api-transport-firm/actions/workflows/ci.yml/badge.svg)](https://github.com/DYyyyDYyy/rest-api-transport-firm/actions/workflows/ci.yml)

REST API for managing the operations of a freight carrier: clients, orders, drivers, vehicles, trip planning and driver trip logs.

**Stack:** Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17, pytest, Docker, GitHub Actions.

The same service is deployed by two other projects: [ansible-infra](https://github.com/DYyyyDYyy/ansible-infra) (rolling deploys to VMs behind nginx, gated on `/health/ready`) and [gitops-platform](https://github.com/DYyyyDYyy/gitops-platform) (Helm chart on Kubernetes, synced by Argo CD).

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

Health checks:

| Endpoint | Description |
|---|---|
| `GET /health` | liveness: the process answers; does not touch the database |
| `GET /health/ready` | readiness: also runs `SELECT 1`; `503` when the database is unreachable |

## Quick start (Docker)

```bash
docker compose up -d --build --wait   # db -> migrate (alembic upgrade head) -> api
curl localhost:8000/health/ready
```

The image is a multi-stage build that runs as a non-root user, with a `HEALTHCHECK` on `/health/ready`. CI publishes it to `ghcr.io/dyyyydyyy/rest-api-transport-firm`.

## Running locally without Docker for the API

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

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push and PR:

| Job | What it checks |
|---|---|
| lint | `ruff check`, `ruff format --check` |
| test | migrations up and down, then `pytest --cov` against a PostgreSQL 17 service container (about 90% coverage) |
| compose | `docker compose up --wait`, then real HTTP requests to the running stack |
| image | the container runs as uid 10001, Trivy scan (fails on fixable CRITICAL), push to GHCR from `main` |

Dependabot keeps pip packages, GitHub Actions and the base image up to date.
