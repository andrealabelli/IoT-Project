from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_admin
from app.config import settings
from app.models.database import get_db
from app.models.entities import Device, Event, Telemetry, User
from app.models.schemas import CalibrationUpdate, DeviceCreate, DeviceOut, IrrigateRequest, TelemetryOut
from app.mqtt.client import mqtt_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
def list_devices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Device).all()


@router.post("", response_model=DeviceOut)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.query(Device).filter(Device.device_id == payload.device_id).first():
        raise HTTPException(status_code=400, detail="device exists")
    d = Device(device_id=payload.device_id, name=payload.name, location=payload.location)
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.get("/{device_id}/latest", response_model=TelemetryOut)
def latest(device_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.query(Telemetry).filter(Telemetry.device_id == device_id).order_by(Telemetry.ts.desc()).first()
    if not row:
        raise HTTPException(status_code=404, detail="No telemetry")
    return row


@router.post("/{device_id}/irrigate")
def irrigate(device_id: str, payload: IrrigateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    command_id = str(uuid4())
    mqtt_service.publish(f"{settings.mqtt_base_topic}/{device_id}/cmd/irrigate", {
        "command_id": command_id,
        "duration_seconds": payload.duration_seconds,
        "timestamp": datetime.utcnow().isoformat(),
    })
    db.add(Event(device_id=device_id, event_type="command", message=f"irrigate {payload.duration_seconds}s", level="info"))
    db.commit()
    return {"sent": True, "command_id": command_id}


@router.post("/{device_id}/refresh")
def refresh(device_id: str, user: User = Depends(get_current_user)):
    command_id = str(uuid4())
    mqtt_service.publish(f"{settings.mqtt_base_topic}/{device_id}/cmd/ping", {"command_id": command_id, "timestamp": datetime.utcnow().isoformat()})
    return {"sent": True, "command_id": command_id}


@router.post("/{device_id}/calibration", response_model=DeviceOut)
def update_calibration(device_id: str, payload: CalibrationUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.soil_offset = payload.soil_offset
    device.temp_offset = payload.temp_offset
    device.humidity_offset = payload.humidity_offset
    db.commit()
    db.refresh(device)
    return device
