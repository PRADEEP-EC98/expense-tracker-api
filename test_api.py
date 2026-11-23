import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


client = TestClient(app)


def add(title="Lunch", amount=120.5, category="Food", spent_on="2026-01-10"):
    return client.post("/expenses", json={"title": title, "amount": amount,
                                          "category": category, "spent_on": spent_on})


def test_health():
    assert client.get("/").json() == {"status": "ok"}


def test_create_and_get():
    r = add()
    assert r.status_code == 201
    eid = r.json()["id"]
    got = client.get(f"/expenses/{eid}")
    assert got.status_code == 200 and got.json()["title"] == "Lunch"


def test_validation_rejects_bad_amount():
    assert add(amount=-5).status_code == 422
    assert add(amount=0).status_code == 422


def test_list_filters():
    add(category="Food", spent_on="2026-01-10")
    add(title="Bus", amount=30, category="Travel", spent_on="2026-02-01")
    assert len(client.get("/expenses").json()) == 2
    assert len(client.get("/expenses", params={"category": "Travel"}).json()) == 1
    assert len(client.get("/expenses", params={"start": "2026-01-15"}).json()) == 1


def test_update_partial():
    eid = add().json()["id"]
    r = client.put(f"/expenses/{eid}", json={"amount": 200})
    assert r.status_code == 200
    assert r.json()["amount"] == 200 and r.json()["title"] == "Lunch"


def test_delete_and_404():
    eid = add().json()["id"]
    assert client.delete(f"/expenses/{eid}").status_code == 204
    assert client.get(f"/expenses/{eid}").status_code == 404
    assert client.delete(f"/expenses/{eid}").status_code == 404


def test_summary_groups_by_category():
    add(amount=100, category="Food")
    add(amount=50, category="Food")
    add(amount=30, category="Travel")
    data = client.get("/expenses/summary").json()
    assert data[0] == {"category": "Food", "total": 150.0, "count": 2}
    assert data[1]["category"] == "Travel"
