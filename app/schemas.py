from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import OrderStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=5, max_length=20)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    address: str | None = Field(default=None, max_length=255)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    email: str | None = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    address: str | None = Field(default=None, max_length=255)


class ClientRead(ClientBase, ORMModel):
    id: int
    created_at: datetime


class DriverBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=5, max_length=20)
    license_number: str = Field(min_length=1, max_length=30)
    license_categories: str = Field(min_length=1, max_length=20)
    experience_years: int = Field(default=0, ge=0, le=60)


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, min_length=5, max_length=20)
    license_number: str | None = Field(default=None, min_length=1, max_length=30)
    license_categories: str | None = Field(default=None, min_length=1, max_length=20)
    experience_years: int | None = Field(default=None, ge=0, le=60)


class DriverRead(DriverBase, ORMModel):
    id: int


class VehicleBase(BaseModel):
    plate_number: str = Field(min_length=1, max_length=15)
    make: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=50)
    capacity_kg: int = Field(gt=0)
    is_available: bool = True
    unavailable_reason: str | None = Field(default=None, max_length=255)


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    plate_number: str | None = Field(default=None, min_length=1, max_length=15)
    make: str | None = Field(default=None, min_length=1, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=50)
    capacity_kg: int | None = Field(default=None, gt=0)
    is_available: bool | None = None
    unavailable_reason: str | None = Field(default=None, max_length=255)


class VehicleRead(VehicleBase, ORMModel):
    id: int


class OrderBase(BaseModel):
    client_id: int
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    status: OrderStatus = OrderStatus.NEW
    notes: str | None = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    client_id: int | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    status: OrderStatus | None = None
    notes: str | None = None


class OrderRead(OrderBase, ORMModel):
    id: int
    created_at: datetime


class TripBase(BaseModel):
    origin: str = Field(min_length=1, max_length=255)
    destination: str = Field(min_length=1, max_length=255)
    distance_km: int = Field(gt=0)
    cargo_weight_kg: int = Field(gt=0)
    planned_start: datetime
    planned_end: datetime


class TripCreate(TripBase):
    order_id: int
    vehicle_id: int | None = None
    driver_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_period(self):
        if self.planned_end <= self.planned_start:
            raise ValueError("planned_end must be later than planned_start")
        return self


class TripUpdate(BaseModel):
    vehicle_id: int | None = None
    driver_ids: list[int] | None = None
    origin: str | None = Field(default=None, min_length=1, max_length=255)
    destination: str | None = Field(default=None, min_length=1, max_length=255)
    distance_km: int | None = Field(default=None, gt=0)
    cargo_weight_kg: int | None = Field(default=None, gt=0)
    planned_start: datetime | None = None
    planned_end: datetime | None = None


class TripRead(TripBase, ORMModel):
    id: int
    order_id: int
    vehicle_id: int | None
    drivers: list[DriverRead]


class TripLogBase(BaseModel):
    trip_id: int
    driver_id: int
    actual_start: datetime
    actual_end: datetime | None = None
    driver_comment: str | None = None

    @model_validator(mode="after")
    def check_period(self):
        if self.actual_end is not None and self.actual_end < self.actual_start:
            raise ValueError("actual_end must not be earlier than actual_start")
        return self


class TripLogCreate(TripLogBase):
    pass


class TripLogUpdate(BaseModel):
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    driver_comment: str | None = None


class TripLogRead(TripLogBase, ORMModel):
    id: int


class DriverTripHistoryItem(ORMModel):
    trip_id: int
    order_id: int
    origin: str
    destination: str
    planned_start: datetime
    planned_end: datetime
    logs: list[TripLogRead]
