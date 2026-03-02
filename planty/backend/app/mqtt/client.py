import json
import logging
from datetime import datetime

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import SessionLocal
from app.models.entities import CommandAck, Device, Event, Telemetry
from app.services.notifications import send_telegram
from app.services.realtime import manager
from app.services.state import StateInput, calculate_state

logger = logging.getLogger(__name__)


class MqttService:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if settings.mqtt_username:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def start(self):
        self.client.connect(settings.mqtt_broker, settings.mqtt_port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        logger.info("MQTT connected with %s", reason_code)
        base = settings.mqtt_base_topic
        client.subscribe(f"{base}/+/telemetry")
        client.subscribe(f"{base}/+/state")
        client.subscribe(f"{base}/+/ack")

    def publish(self, topic: str, payload: dict):
        self.client.publish(topic, json.dumps(payload), qos=1)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            return
        parts = msg.topic.split("/")
        if len(parts) < 3:
            return
        device_id = parts[1]
        kind = parts[2]
        db: Session = SessionLocal()
        try:
            if kind == "telemetry":
                self._handle_telemetry(db, device_id, payload)
            elif kind == "ack":
                self._handle_ack(db, device_id, payload)
        finally:
            db.close()

    def _handle_telemetry(self, db: Session, device_id: str, payload: dict):
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            db.add(Event(device_id=device_id, event_type="error", level="warning", message="Unknown device telemetry"))
            db.commit()
            return
        telemetry = Telemetry(
            device_id=device_id,
            ts=datetime.fromisoformat(payload.get("timestamp")) if payload.get("timestamp") else datetime.utcnow(),
            air_temperature=payload.get("air_temperature", 0) + device.temp_offset,
            air_humidity=payload.get("air_humidity", 0) + device.humidity_offset,
            soil_moisture=payload.get("soil_moisture", 0) + device.soil_offset,
            battery_voltage=payload.get("battery_voltage"),
            source="device",
        )
        telemetry.state = calculate_state(
            StateInput(
                soil_moisture=telemetry.soil_moisture,
                air_temperature=telemetry.air_temperature,
                air_humidity=telemetry.air_humidity,
                soil_threshold=device.soil_threshold,
                temp_min=device.air_temp_min,
                temp_max=device.air_temp_max,
                humidity_min=device.air_humidity_min,
                humidity_max=device.air_humidity_max,
            )
        )
        db.add(telemetry)
        db.add(Event(device_id=device_id, event_type="telemetry", message=f"State={telemetry.state.value}", level="info"))
        db.commit()
        if telemetry.state.value in {"NEEDS_WATER", "MOVE_PLANT", "SENSOR_ERROR"}:
            import asyncio

            asyncio.run(send_telegram(f"Planty alert {device_id}: {telemetry.state.value}"))
        import asyncio

        asyncio.run(manager.publish(device_id, {
            "type": "telemetry",
            "air_temperature": telemetry.air_temperature,
            "air_humidity": telemetry.air_humidity,
            "soil_moisture": telemetry.soil_moisture,
            "state": telemetry.state.value,
            "timestamp": telemetry.ts.isoformat(),
        }))

    def _handle_ack(self, db: Session, device_id: str, payload: dict):
        ack = CommandAck(
            device_id=device_id,
            command=payload.get("command", "unknown"),
            command_id=payload.get("command_id", "n/a"),
            success=bool(payload.get("success", False)),
            details=payload.get("details"),
        )
        db.add(ack)
        db.add(Event(device_id=device_id, event_type="ack", level="info", message=json.dumps(payload)))
        db.commit()


mqtt_service = MqttService()
