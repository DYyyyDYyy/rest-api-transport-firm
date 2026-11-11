from fastapi import Depends, FastAPI, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import clients, drivers, orders, trip_logs, trips, vehicles

app = FastAPI(
    title="Transport Firm API",
    description="REST API for managing orders, clients, drivers, vehicles and trips of a freight carrier.",
    version="1.0.0",
)

for module in (clients, drivers, vehicles, orders, trips, trip_logs):
    app.include_router(module.router)


@app.get("/health", tags=["health"])
def health():
    """Liveness: the process is up and serving requests. Does not touch the database."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def ready(response: Response, db: Session = Depends(get_db)):
    """Readiness: the API can also reach the database, so it can serve real requests.

    Returns 503 when the database is unreachable, so a load balancer or a deploy
    script can tell "process up" from "able to answer".
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "unreachable"}
    return {"status": "ok", "database": "ok"}
