from datetime import UTC, datetime, timedelta

from app.database import SessionLocal
from app.models import Client, Driver, Order, OrderStatus, TripDetails, TripLog, Vehicle


def main() -> None:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        if db.query(Client).count():
            print("Database already contains data, skipping")
            return

        clients = [
            Client(
                name="Fresh Market LLC",
                phone="+380441234567",
                email="ops@freshmarket.ua",
                address="Kyiv, Khreshchatyk 22",
            ),
            Client(name="BuildPro", phone="+380322223344", email="logistics@buildpro.ua", address="Lviv, Stryiska 108"),
            Client(
                name="AgroTrade", phone="+380482445566", email="dispatch@agrotrade.ua", address="Odesa, Prymorska 5"
            ),
        ]
        drivers = [
            Driver(
                full_name="Ivan Petrenko",
                phone="+380501112233",
                license_number="AB123456",
                license_categories="C,CE",
                experience_years=8,
            ),
            Driver(
                full_name="Olena Koval",
                phone="+380509998877",
                license_number="CD654321",
                license_categories="B,C",
                experience_years=4,
            ),
            Driver(
                full_name="Andrii Melnyk",
                phone="+380671230099",
                license_number="EF112233",
                license_categories="C,CE",
                experience_years=12,
            ),
        ]
        vehicles = [
            Vehicle(plate_number="AA1234BB", make="MAN", model="TGX", capacity_kg=20000),
            Vehicle(plate_number="BC5678KT", make="Volvo", model="FH", capacity_kg=18000),
            Vehicle(plate_number="KA4321IH", make="Mercedes-Benz", model="Sprinter", capacity_kg=1800),
            Vehicle(
                plate_number="AX9090AX",
                make="DAF",
                model="XF",
                capacity_kg=19000,
                is_available=False,
                unavailable_reason="Scheduled maintenance",
            ),
        ]
        db.add_all([*clients, *drivers, *vehicles])
        db.flush()

        orders = [
            Order(
                client_id=clients[0].id,
                price=1850.50,
                status=OrderStatus.COMPLETED,
                created_at=now - timedelta(days=12),
            ),
            Order(
                client_id=clients[1].id, price=3200, status=OrderStatus.IN_PROGRESS, created_at=now - timedelta(days=2)
            ),
            Order(client_id=clients[2].id, price=980, status=OrderStatus.NEW, created_at=now - timedelta(days=1)),
        ]
        db.add_all(orders)
        db.flush()

        done = TripDetails(
            order_id=orders[0].id,
            vehicle_id=vehicles[0].id,
            origin="Kyiv",
            destination="Lviv",
            distance_km=540,
            cargo_weight_kg=12000,
            planned_start=now - timedelta(days=11),
            planned_end=now - timedelta(days=11) + timedelta(hours=9),
            drivers=[drivers[0]],
        )
        active = TripDetails(
            order_id=orders[1].id,
            vehicle_id=vehicles[1].id,
            origin="Lviv",
            destination="Odesa",
            distance_km=790,
            cargo_weight_kg=15000,
            planned_start=now - timedelta(hours=6),
            planned_end=now + timedelta(hours=8),
            drivers=[drivers[0], drivers[2]],
        )
        db.add_all([done, active])
        db.flush()

        db.add_all(
            [
                TripLog(
                    trip_id=done.id,
                    driver_id=drivers[0].id,
                    actual_start=done.planned_start + timedelta(minutes=15),
                    actual_end=done.planned_end + timedelta(minutes=40),
                    driver_comment="Delay at the Zhytomyr bypass",
                ),
                TripLog(
                    trip_id=active.id,
                    driver_id=drivers[2].id,
                    actual_start=active.planned_start + timedelta(minutes=5),
                    driver_comment="Departed on time",
                ),
            ]
        )
        db.commit()
        print("Seed data created")


if __name__ == "__main__":
    main()
