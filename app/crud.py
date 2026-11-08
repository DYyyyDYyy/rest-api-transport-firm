from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base

T = TypeVar("T", bound=Base)


def get_or_404(db: Session, model: type[T], obj_id: int) -> T:
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} {obj_id} not found")
    return obj


def commit_or_409(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        diag = getattr(exc.orig, "diag", None)
        detail = diag.message_detail if diag and diag.message_detail else str(exc.orig)
        raise HTTPException(status.HTTP_409_CONFLICT, detail.strip()) from exc


def apply_update(obj: Base, data: dict) -> None:
    for field, value in data.items():
        setattr(obj, field, value)
