from fastapi import FastAPI

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
    return {"status": "ok"}
