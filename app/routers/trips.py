from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.crud import apply_update, commit_or_409, get_or_404
from app.database import get_db
from app.models import Driver, Order, TripDetails, Vehicle

router = APIRouter(prefix="/trips", tags=["trips"])


def load_drivers(db: Session, driver_ids: list[int]) -> list[Driver]:
    ids = set(driver_ids)
    drivers = list(db.scalars(select(Driver).where(Driver.id.in_(ids))).all())
    missing = ids - {d.id for d in drivers}
    if missing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Drivers not found: {sorted(missing)}")
    return drivers


def check_vehicle(db: Session, vehicle_id: int, cargo_weight_kg: int, current_trip_id: int | None = None) -> None:
    vehicle = get_or_404(db, Vehicle, vehicle_id)
    reassigned = current_trip_id is not None and any(t.id == current_trip_id for t in vehicle.trips)
    if not vehicle.is_available and not reassigned:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Vehicle {vehicle_id} is not available")
    if cargo_weight_kg > vehicle.capacity_kg:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Cargo ({cargo_weight_kg} kg) exceeds vehicle capacity ({vehicle.capacity_kg} kg)",
        )


@router.get("", response_model=list[schemas.TripRead])
def list_trips(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    return db.scalars(select(TripDetails).order_by(TripDetails.id).offset(skip).limit(limit)).all()


@router.post("", response_model=schemas.TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(payload: schemas.TripCreate, db: Session = Depends(get_db)):
    get_or_404(db, Order, payload.order_id)
    if payload.vehicle_id is not None:
        check_vehicle(db, payload.vehicle_id, payload.cargo_weight_kg)
    data = payload.model_dump(exclude={"driver_ids"})
    trip = TripDetails(**data, drivers=load_drivers(db, payload.driver_ids))
    db.add(trip)
    commit_or_409(db)
    return trip


@router.get("/{trip_id}", response_model=schemas.TripRead)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, TripDetails, trip_id)


@router.patch("/{trip_id}", response_model=schemas.TripRead)
def update_trip(trip_id: int, payload: schemas.TripUpdate, db: Session = Depends(get_db)):
    trip = get_or_404(db, TripDetails, trip_id)
    data = payload.model_dump(exclude_unset=True)
    driver_ids = data.pop("driver_ids", None)

    weight = data.get("cargo_weight_kg", trip.cargo_weight_kg)
    vehicle_id = data.get("vehicle_id", trip.vehicle_id)
    if vehicle_id is not None and ("vehicle_id" in data or "cargo_weight_kg" in data):
        check_vehicle(db, vehicle_id, weight, current_trip_id=trip.id)
    if driver_ids is not None:
        trip.drivers = load_drivers(db, driver_ids)

    apply_update(trip, data)
    commit_or_409(db)
    return trip


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, TripDetails, trip_id))
    commit_or_409(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
