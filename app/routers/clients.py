from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import schemas
from app.crud import apply_update, commit_or_409, get_or_404
from app.database import get_db
from app.models import Client

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[schemas.ClientRead])
def list_clients(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    return db.scalars(select(Client).order_by(Client.id).offset(skip).limit(limit)).all()


@router.post("", response_model=schemas.ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    client = Client(**payload.model_dump())
    db.add(client)
    commit_or_409(db)
    return client


@router.get("/{client_id}", response_model=schemas.ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Client, client_id)


@router.patch("/{client_id}", response_model=schemas.ClientRead)
def update_client(client_id: int, payload: schemas.ClientUpdate, db: Session = Depends(get_db)):
    client = get_or_404(db, Client, client_id)
    apply_update(client, payload.model_dump(exclude_unset=True))
    commit_or_409(db)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    db.delete(get_or_404(db, Client, client_id))
    commit_or_409(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
