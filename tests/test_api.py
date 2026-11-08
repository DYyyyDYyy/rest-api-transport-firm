from tests.conftest import make

TRIP_WINDOW = {"planned_start": "2026-11-10T08:00:00Z", "planned_end": "2026-11-10T18:00:00Z"}


def new_trip(client, seed, **overrides):
    payload = {
        "order_id": seed["order"]["id"],
        "vehicle_id": seed["vehicle"]["id"],
        "driver_ids": [seed["driver"]["id"]],
        "origin": "Kyiv",
        "destination": "Lviv",
        "distance_km": 540,
        "cargo_weight_kg": 12000,
        **TRIP_WINDOW,
        **overrides,
    }
    return client.post("/trips", json=payload)


def test_client_crud(client):
    created = make(client, "/clients", {"name": "Acme", "phone": "+380671234567", "email": "acme@example.com"})
    cid = created["id"]
    assert client.get(f"/clients/{cid}").json()["name"] == "Acme"
    patched = client.patch(f"/clients/{cid}", json={"address": "Odesa"})
    assert patched.json()["address"] == "Odesa"
    assert len(client.get("/clients").json()) == 1
    assert client.delete(f"/clients/{cid}").status_code == 204
    assert client.get(f"/clients/{cid}").status_code == 404


def test_duplicate_email_conflict(client):
    payload = {"name": "A", "phone": "+380671234567", "email": "dup@example.com"}
    make(client, "/clients", payload)
    assert client.post("/clients", json=payload).status_code == 409


def test_validation_errors(client):
    assert client.post("/clients", json={"name": "A", "phone": "+380671234567", "email": "bad"}).status_code == 422
    assert client.post("/vehicles", json={"plate_number": "X", "make": "M", "model": "T", "capacity_kg": 0}).status_code == 422


def test_client_with_orders_cannot_be_deleted(client, seed):
    assert client.delete(f"/clients/{seed['client']['id']}").status_code == 409


def test_order_requires_existing_client(client):
    response = client.post("/orders", json={"client_id": 999, "price": "10"})
    assert response.status_code == 404


def test_trip_lifecycle_with_log_and_history(client, seed):
    response = new_trip(client, seed)
    assert response.status_code == 201
    trip = response.json()
    assert trip["drivers"][0]["id"] == seed["driver"]["id"]

    log = make(client, "/trip-logs", {
        "trip_id": trip["id"],
        "driver_id": seed["driver"]["id"],
        "actual_start": "2026-11-10T08:15:00Z",
        "actual_end": "2026-11-10T17:40:00Z",
        "driver_comment": "Traffic near Zhytomyr",
    })

    history = client.get(f"/drivers/{seed['driver']['id']}/trips").json()
    assert len(history) == 1
    assert history[0]["destination"] == "Lviv"
    assert history[0]["logs"][0]["id"] == log["id"]

    assert client.delete(f"/orders/{seed['order']['id']}").status_code == 204
    assert client.get(f"/trips/{trip['id']}").status_code == 404
    assert client.get("/trip-logs").json() == []


def test_one_trip_per_order(client, seed):
    assert new_trip(client, seed).status_code == 201
    assert new_trip(client, seed).status_code == 409


def test_cargo_over_capacity_rejected(client, seed):
    assert new_trip(client, seed, cargo_weight_kg=25000).status_code == 422


def test_trip_period_validated(client, seed):
    response = new_trip(client, seed, planned_end="2026-11-10T07:00:00Z")
    assert response.status_code == 422


def test_unavailable_vehicle_rejected(client, seed):
    client.patch(f"/vehicles/{seed['vehicle']['id']}", json={"is_available": False, "unavailable_reason": "Engine repair"})
    assert new_trip(client, seed).status_code == 409


def test_log_requires_assigned_driver(client, seed):
    trip = new_trip(client, seed).json()
    other = make(client, "/drivers", {"full_name": "Olena Koval", "phone": "+380509998877", "license_number": "CD654321", "license_categories": "B,C"})
    response = client.post("/trip-logs", json={
        "trip_id": trip["id"], "driver_id": other["id"], "actual_start": "2026-11-10T08:00:00Z",
    })
    assert response.status_code == 409


def test_log_end_before_start_rejected(client, seed):
    trip = new_trip(client, seed).json()
    response = client.post("/trip-logs", json={
        "trip_id": trip["id"], "driver_id": seed["driver"]["id"],
        "actual_start": "2026-11-10T10:00:00Z", "actual_end": "2026-11-10T09:00:00Z",
    })
    assert response.status_code == 422


def test_available_vehicles(client, seed):
    broken = make(client, "/vehicles", {"plate_number": "BB9999CC", "make": "Volvo", "model": "FH", "capacity_kg": 18000, "is_available": False, "unavailable_reason": "In service"})
    busy = make(client, "/vehicles", {"plate_number": "CC5555DD", "make": "DAF", "model": "XF", "capacity_kg": 19000})

    ids = {v["id"] for v in client.get("/vehicles/available").json()}
    assert ids == {seed["vehicle"]["id"], busy["id"]}

    trip = new_trip(client, seed, vehicle_id=busy["id"]).json()
    client.patch(f"/orders/{seed['order']['id']}", json={"status": "in_progress"})
    ids = {v["id"] for v in client.get("/vehicles/available").json()}
    assert ids == {seed["vehicle"]["id"]}
    assert broken["id"] not in ids and trip["vehicle_id"] == busy["id"]


def test_orders_in_period(client, seed):
    today = client.get(f"/orders/{seed['order']['id']}").json()["created_at"][:10]
    found = client.get("/orders/period", params={"date_from": today, "date_to": today}).json()
    assert [o["id"] for o in found] == [seed["order"]["id"]]
    assert client.get("/orders/period", params={"date_from": "2000-01-01", "date_to": "2000-01-31"}).json() == []
    assert client.get("/orders/period", params={"date_from": "2026-02-01", "date_to": "2026-01-01"}).status_code == 422


def test_referenced_records_cannot_be_deleted(client, seed):
    new_trip(client, seed)
    response = client.delete(f"/clients/{seed['client']['id']}")
    assert response.status_code == 409
    assert "is referenced from table" in response.json()["detail"]
    assert client.delete(f"/vehicles/{seed['vehicle']['id']}").status_code == 409
    assert client.delete(f"/drivers/{seed['driver']['id']}").status_code == 409
