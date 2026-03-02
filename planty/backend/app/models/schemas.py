from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.entities import PlantState, Role


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: Role = Role.USER


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: Role

    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    device_id: str
    name: str
    location: Optional[str] = None


class DeviceOut(BaseModel):
    id: int
    device_id: str
    name: str
    location: Optional[str]
    publish_interval_seconds: int
    soil_threshold: float
    air_temp_min: float
    air_temp_max: float
    air_humidity_min: float
    air_humidity_max: float
    lockout_seconds: int
    pump_duration_seconds: int
    soil_offset: float
    temp_offset: float
    humidity_offset: float

    class Config:
        from_attributes = True


class CalibrationUpdate(BaseModel):
    soil_offset: float = 0
    temp_offset: float = 0
    humidity_offset: float = 0


class TelemetryOut(BaseModel):
    device_id: str
    ts: datetime
    air_temperature: float
    air_humidity: float
    soil_moisture: float
    battery_voltage: float | None
    state: PlantState

    class Config:
        from_attributes = True


class IrrigateRequest(BaseModel):
    duration_seconds: int = 5


class EventOut(BaseModel):
    id: int
    device_id: str | None
    level: str
    message: str
    event_type: str
    ts: datetime

    class Config:
        from_attributes = True
