import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(str, enum.Enum):
    NEW = "new"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


trip_drivers = Table(
    "trip_drivers",
    Base.metadata,
    Column("trip_id", ForeignKey("trip_details.id", ondelete="CASCADE"), primary_key=True),
    Column("driver_id", ForeignKey("drivers.id", ondelete="RESTRICT"), primary_key=True),
)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    address: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders: Mapped[list["Order"]] = relationship(back_populates="client")


class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = (CheckConstraint("experience_years >= 0", name="ck_drivers_experience"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150))
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    license_number: Mapped[str] = mapped_column(String(30), unique=True)
    license_categories: Mapped[str] = mapped_column(String(20))
    experience_years: Mapped[int] = mapped_column(default=0)

    trips: Mapped[list["TripDetails"]] = relationship(
        secondary=trip_drivers, back_populates="drivers"
    )
    logs: Mapped[list["TripLog"]] = relationship(back_populates="driver")


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (CheckConstraint("capacity_kg > 0", name="ck_vehicles_capacity"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plate_number: Mapped[str] = mapped_column(String(15), unique=True)
    make: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    capacity_kg: Mapped[int]
    is_available: Mapped[bool] = mapped_column(default=True, server_default="true")
    unavailable_reason: Mapped[str | None] = mapped_column(String(255))

    trips: Mapped[list["TripDetails"]] = relationship(back_populates="vehicle")


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (CheckConstraint("price >= 0", name="ck_orders_price"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="RESTRICT"))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]),
        default=OrderStatus.NEW,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped[Client] = relationship(back_populates="orders")
    trip: Mapped["TripDetails | None"] = relationship(
        back_populates="order", uselist=False, cascade="all, delete-orphan"
    )


class TripDetails(Base):
    __tablename__ = "trip_details"
    __table_args__ = (
        CheckConstraint("planned_end > planned_start", name="ck_trip_details_period"),
        CheckConstraint("distance_km > 0", name="ck_trip_details_distance"),
        CheckConstraint("cargo_weight_kg > 0", name="ck_trip_details_weight"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id", ondelete="RESTRICT"))
    origin: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    distance_km: Mapped[int]
    cargo_weight_kg: Mapped[int]
    planned_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    planned_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    order: Mapped[Order] = relationship(back_populates="trip")
    vehicle: Mapped[Vehicle | None] = relationship(back_populates="trips")
    drivers: Mapped[list[Driver]] = relationship(secondary=trip_drivers, back_populates="trips")
    logs: Mapped[list["TripLog"]] = relationship(back_populates="trip", cascade="all, delete-orphan")


class TripLog(Base):
    __tablename__ = "trip_logs"
    __table_args__ = (
        CheckConstraint("actual_end IS NULL OR actual_end >= actual_start", name="ck_trip_logs_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trip_details.id", ondelete="CASCADE"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id", ondelete="RESTRICT"))
    actual_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actual_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    driver_comment: Mapped[str | None] = mapped_column(Text)

    trip: Mapped[TripDetails] = relationship(back_populates="logs")
    driver: Mapped[Driver] = relationship(back_populates="logs")
