import asyncio
import json
import logging
import time
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
        retries = 0
        while True:
            try:
                self.client.connect(settings.mqtt_broker, settings.mqtt_port, 60)
                self.client.loop_start()
                logger.info("MQTT loop started")
                return
            except Exception as exc:
                retries += 1
                wait_s = min(2 * retries, 15)
                logger.warning("MQTT connect failed (attempt %s): %s", retries, exc)
                time.sleep(wait_s)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        base = settings.mqtt_base_topic
        client.subscribe(f"{base}/+/telemetry")
        client.subscribe(f"{base}/+/ack")

    def publish(self, topic: str, payload: dict):
        self.client.publish(topic, json.dumps(payload), qos=1)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            parts = msg.topic.split("/")
            device_id, kind = parts[1], parts[2]
        except Exception:
            return

        db: Session = SessionLocal()
        try:
            if kind == "telemetry":
                self._handle_telemetry(db, device_id, payload)
            elif kind == "ack":
                self._handle_ack(db, device_id, payload)
        finally:
            db.close()

    def _parse_ts(self, raw):
        if not raw:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()

    def _handle_telemetry(self, db: Session, device_id: str, payload: dict):
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            db.add(Event(device_id=device_id, level="warning", event_type="error", message="Unknown device telemetry"))
            db.commit()
            return

        air_t = float(payload.get("t_c", payload.get("air_temperature", 0))) + device.temp_offset
        air_h = float(payload.get("rh", payload.get("air_humidity", 0))) + device.humidity_offset
        soil = float(payload.get("soil_pct", payload.get("soil_moisture", 0))) + device.soil_offset
        telemetry = Telemetry(
            device_id=device_id,
            ts=self._parse_ts(payload.get("ts") or payload.get("timestamp")),
            air_temperature=air_t,
            air_humidity=air_h,
            soil_moisture=soil,
            battery_voltage=payload.get("battery_voltage"),
            source="device",
        )
        telemetry.state = calculate_state(
            StateInput(
                soil_moisture=soil,
                air_temperature=air_t,
                air_humidity=air_h,
                soil_threshold=device.soil_threshold,
                temp_min=device.air_temp_min,
                temp_max=device.air_temp_max,
                humidity_min=device.air_humidity_min,
                humidity_max=device.air_humidity_max,
            )
        )
        db.add(telemetry)
        db.add(Event(device_id=device_id, event_type="telemetry", level="info", message=f"State={telemetry.state.value}"))
        db.commit()

        if telemetry.state.value in {"NEEDS_WATER", "MOVE_PLANT", "SENSOR_ERROR"}:
            asyncio.run(send_telegram(f"Planty alert {device_id}: {telemetry.state.value}"))

        asyncio.run(
            manager.publish(
                device_id,
                {
                    "type": "telemetry",
                    "air_temperature": telemetry.air_temperature,
                    "air_humidity": telemetry.air_humidity,
                    "soil_moisture": telemetry.soil_moisture,
                    "state": telemetry.state.value,
                    "timestamp": telemetry.ts.isoformat(),
                },
            )
        )

    def _handle_ack(self, db: Session, device_id: str, payload: dict):
        cmd = payload.get("cmd", payload.get("command", "unknown"))
        result = payload.get("result", "ERR")
        cmd_id = payload.get("cmd_id", payload.get("command_id", "n/a"))
        success = str(result).upper() == "OK"
        details = payload.get("reason") or payload.get("details")

        db.add(CommandAck(device_id=device_id, command=cmd, command_id=cmd_id, success=success, details=details))
        db.add(Event(device_id=device_id, event_type="ack", level="info", message=json.dumps(payload)))
        db.commit()

        asyncio.run(
            manager.publish(
                device_id,
                {"type": "ack", "command": cmd, "command_id": cmd_id, "success": success, "details": details},
            )
        )


mqtt_service = MqttService()
