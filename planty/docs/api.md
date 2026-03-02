# API & MQTT

## REST
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /devices`
- `POST /devices`
- `GET /devices/{id}/latest`
- `POST /devices/{id}/irrigate`
- `POST /devices/{id}/refresh`
- `POST /devices/{id}/calibration`
- `GET /events`

## MQTT payloads
### telemetry (`planty/<deviceId>/telemetry`)
```json
{ "ts":"2026-01-10T10:20:00Z", "t_c":23.1, "rh":45.2, "soil_pct":31, "state":"NEEDS_WATER", "flags":["OK"] }
```

### ack (`planty/<deviceId>/ack`)
```json
{ "ts":"2026-01-10T10:20:03Z", "cmd":"IRRIGATE", "cmd_id":"abc-123", "result":"OK" }
```

## WebSocket
- `GET ws://<backend>/ws/{deviceId}`
- push messaggi:
  - `{"type":"telemetry", ...}`
  - `{"type":"ack", "command":"IRRIGATE", "success":true, ...}`
