from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.database import Base


class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"


class PlantState(str, Enum):
    OK = "OK"
    NEEDS_WATER = "NEEDS_WATER"
    MOVE_PLANT = "MOVE_PLANT"
    SENSOR_ERROR = "SENSOR_ERROR"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SqlEnum(Role), default=Role.USER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True)
    device_id = Column(String(80), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    location = Column(String(120), nullable=True)
    publish_interval_seconds = Column(Integer, default=10)
    soil_threshold = Column(Float, default=35.0)
    air_temp_min = Column(Float, default=15.0)
    air_temp_max = Column(Float, default=30.0)
    air_humidity_min = Column(Float, default=30.0)
    air_humidity_max = Column(Float, default=75.0)
    lockout_seconds = Column(Integer, default=180)
    pump_duration_seconds = Column(Integer, default=5)
    soil_offset = Column(Float, default=0.0)
    temp_offset = Column(Float, default=0.0)
    humidity_offset = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    telemetry = relationship("Telemetry", back_populates="device", cascade="all,delete")


class Telemetry(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True)
    device_id = Column(String(80), ForeignKey("devices.device_id"), nullable=False, index=True)
    ts = Column(DateTime, default=datetime.utcnow, index=True)
    air_temperature = Column(Float, nullable=False)
    air_humidity = Column(Float, nullable=False)
    soil_moisture = Column(Float, nullable=False)
    battery_voltage = Column(Float, nullable=True)
    state = Column(SqlEnum(PlantState), default=PlantState.OK)
    source = Column(String(32), default="device")

    device = relationship("Device", back_populates="telemetry")


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    device_id = Column(String(80), nullable=True)
    level = Column(String(32), default="info")
    message = Column(Text, nullable=False)
    event_type = Column(String(32), nullable=False)
    ts = Column(DateTime, default=datetime.utcnow)


class CommandAck(Base):
    __tablename__ = "command_acks"
    id = Column(Integer, primary_key=True)
    device_id = Column(String(80), nullable=False, index=True)
    command = Column(String(64), nullable=False)
    command_id = Column(String(64), nullable=False, index=True)
    success = Column(Boolean, default=False)
    details = Column(Text, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)
