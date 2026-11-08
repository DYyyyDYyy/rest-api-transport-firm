from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import schemas
from app.crud import apply_update, commit_or_409, get_or_404
from app.database import get_db
from app.models import Driver, TripDetails, trip_drivers

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("", response_model=list[schemas.DriverRead])
def list_drivers(
    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)
):
    return db.scalars(select(Driver).order_by(Driver.id).offset(skip).limit(limit)).all()


@router.post("", response_model=schemas.DriverRead, status_code=status.HTTP_201_CREATED)
def create_driver(payload: schemas.DriverCreate, db: Session = Depends(get_db)):
    driver = Driver(**payload.model_dump())
    db.add(driver)
    commit_or_409(db)
    return driver


@router.get("/{driver_id}", response_model=schemas.DriverRead)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Driver, driver_id)


@router.get("/{driver_id}/trips", response_model=list[schemas.DriverTripHistoryItem])
def driver_trip_history(driver_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Driver, driver_id)
    trips = db.scalars(
        select(TripDetails)
        .join(trip_drivers, trip_drivers.c.trip_id == TripDetails.id)
        .where(trip_drivers.c.driver_id == driver_id)
        .options(selectinload(TripDetails.logs))
        .order_by(TripDetails.planned_start.desc())
    ).all()
    return [
        schemas.DriverTripHistoryItem(
            trip_id=t.id,
            order_id=t.order_id,
            origin=t.origin,
            destination=t.destination,
            planned_start=t.planned_start,
            planned_end=t.planned_end,
            logs=[log for log in t.logs if log.driver_id == driver_id],
        )
        for t in trips
    ]


@router.patch("/{driver_id}", response_model=schemas.DriverRead)
def update_driver(driver_id: int, payload: schemas.DriverUpdate, db: Session = Depends(get_db)):
    driver = get_or_404(db, Driver, driver_id)
    apply_update(driver, payload.model_dump(exclude_unset=True))
    commit_or_409(db)
    return driver


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, Driver, driver_id))
    commit_or_409(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
