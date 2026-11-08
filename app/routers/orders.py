from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.crud import apply_update, commit_or_409, get_or_404
from app.database import get_db
from app.models import Client, Order, OrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=list[schemas.OrderRead])
def list_orders(
    status_filter: OrderStatus | None = Query(None, alias="status"),
    client_id: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(Order).order_by(Order.id).offset(skip).limit(limit)
    if status_filter:
        query = query.where(Order.status == status_filter)
    if client_id:
        query = query.where(Order.client_id == client_id)
    return db.scalars(query).all()


@router.get("/period", response_model=list[schemas.OrderRead])
def orders_in_period(date_from: date, date_to: date, db: Session = Depends(get_db)):
    if date_to < date_from:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "date_to must not be earlier than date_from")
    start = datetime.combine(date_from, time.min, tzinfo=UTC)
    end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC)
    return db.scalars(
        select(Order)
        .where(Order.created_at >= start, Order.created_at < end)
        .order_by(Order.created_at)
    ).all()


@router.post("", response_model=schemas.OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db)):
    get_or_404(db, Client, payload.client_id)
    order = Order(**payload.model_dump())
    db.add(order)
    commit_or_409(db)
    return order


@router.get("/{order_id}", response_model=schemas.OrderRead)
def get_order(order_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Order, order_id)


@router.patch("/{order_id}", response_model=schemas.OrderRead)
def update_order(order_id: int, payload: schemas.OrderUpdate, db: Session = Depends(get_db)):
    order = get_or_404(db, Order, order_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("client_id") is not None:
        get_or_404(db, Client, data["client_id"])
    apply_update(order, data)
    commit_or_409(db)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, Order, order_id))
    commit_or_409(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
