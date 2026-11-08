from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.crud import apply_update, commit_or_409, get_or_404
from app.database import get_db
from app.models import Driver, TripDetails, TripLog

router = APIRouter(prefix="/trip-logs", tags=["trip-logs"])


@router.get("", response_model=list[schemas.TripLogRead])
def list_trip_logs(
    trip_id: int | None = None,
    driver_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(TripLog).order_by(TripLog.id).offset(skip).limit(limit)
    if trip_id:
        query = query.where(TripLog.trip_id == trip_id)
    if driver_id:
        query = query.where(TripLog.driver_id == driver_id)
    return db.scalars(query).all()


@router.post("", response_model=schemas.TripLogRead, status_code=status.HTTP_201_CREATED)
def create_trip_log(payload: schemas.TripLogCreate, db: Session = Depends(get_db)):
    trip = get_or_404(db, TripDetails, payload.trip_id)
    driver = get_or_404(db, Driver, payload.driver_id)
    if driver not in trip.drivers:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Driver {driver.id} is not assigned to trip {trip.id}")
    log = TripLog(**payload.model_dump())
    db.add(log)
    commit_or_409(db)
    return log


@router.get("/{log_id}", response_model=schemas.TripLogRead)
def get_trip_log(log_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, TripLog, log_id)


@router.patch("/{log_id}", response_model=schemas.TripLogRead)
def update_trip_log(log_id: int, payload: schemas.TripLogUpdate, db: Session = Depends(get_db)):
    log = get_or_404(db, TripLog, log_id)
    data = payload.model_dump(exclude_unset=True)
    start = data.get("actual_start", log.actual_start)
    end = data.get("actual_end", log.actual_end)
    if end is not None and end < start:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "actual_end must not be earlier than actual_start")
    apply_update(log, data)
    commit_or_409(db)
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip_log(log_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, TripLog, log_id))
    commit_or_409(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
