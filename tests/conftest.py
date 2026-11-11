import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.config import Settings
from app.database import Base, get_db
from app.main import app

TEST_URL = os.getenv("TEST_DATABASE_URL") or Settings().database_url.rsplit("/", 1)[0] + "/transport_firm_test"


@pytest.fixture()
def client():
    engine = create_engine(TEST_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def make(client, path, payload):
    response = client.post(path, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def seed(client):
    customer = make(
        client, "/clients", {"name": "Fresh Market LLC", "phone": "+380441234567", "email": "ops@freshmarket.ua"}
    )
    driver = make(
        client,
        "/drivers",
        {
            "full_name": "Ivan Petrenko",
            "phone": "+380501112233",
            "license_number": "AB123456",
            "license_categories": "C,CE",
            "experience_years": 8,
        },
    )
    vehicle = make(
        client, "/vehicles", {"plate_number": "AA1234BB", "make": "MAN", "model": "TGX", "capacity_kg": 20000}
    )
    order = make(client, "/orders", {"client_id": customer["id"], "price": "1850.50"})
    return {"client": customer, "driver": driver, "vehicle": vehicle, "order": order}
