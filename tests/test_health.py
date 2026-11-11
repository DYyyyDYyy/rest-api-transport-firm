from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app


def test_liveness(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_when_database_is_up(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_not_ready_when_database_is_down(client):
    # Nothing listens on port 1: the connection is refused immediately.
    engine = create_engine("postgresql+psycopg2://nobody:nothing@127.0.0.1:1/missing")
    Session = sessionmaker(bind=engine)

    def unreachable_db():
        with Session() as session:
            yield session

    app.dependency_overrides[get_db] = unreachable_db
    response = client.get("/health/ready")
    engine.dispose()

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unreachable"}
    # liveness does not depend on the database
    assert client.get("/health").status_code == 200
