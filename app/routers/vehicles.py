from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app import schemas
from app.crud import apply_update, commit_or_409, get_or_404
from app.database import get_db
from app.models import Order, OrderStatus, TripDetails, Vehicle

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[schemas.VehicleRead])
def list_vehicles(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    return db.scalars(select(Vehicle).order_by(Vehicle.id).offset(skip).limit(limit)).all()


@router.get("/available", response_model=list[schemas.VehicleRead])
def list_available_vehicles(db: Session = Depends(get_db)):
    on_trip = exists().where(
        TripDetails.vehicle_id == Vehicle.id,
        TripDetails.order_id == Order.id,
        Order.status == OrderStatus.IN_PROGRESS,
    )
    return db.scalars(select(Vehicle).where(Vehicle.is_available.is_(True), ~on_trip).order_by(Vehicle.id)).all()


@router.post("", response_model=schemas.VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(payload: schemas.VehicleCreate, db: Session = Depends(get_db)):
    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    commit_or_409(db)
    return vehicle


@router.get("/{vehicle_id}", response_model=schemas.VehicleRead)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Vehicle, vehicle_id)


@router.patch("/{vehicle_id}", response_model=schemas.VehicleRead)
def update_vehicle(vehicle_id: int, payload: schemas.VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = get_or_404(db, Vehicle, vehicle_id)
    apply_update(vehicle, payload.model_dump(exclude_unset=True))
    commit_or_409(db)
    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, Vehicle, vehicle_id))
    commit_or_409(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
