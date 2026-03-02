# API & MQTT

## REST
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /devices`
- `POST /devices` (admin)
- `GET /devices/{id}/latest`
- `POST /devices/{id}/irrigate`
- `POST /devices/{id}/refresh`
- `POST /devices/{id}/calibration`
- `GET /events`

## MQTT Topics
- `planty/{deviceId}/telemetry`
- `planty/{deviceId}/state`
- `planty/{deviceId}/cmd/irrigate`
- `planty/{deviceId}/cmd/ping`
- `planty/{deviceId}/ack`

Payload JSON con timestamp ISO8601 lato backend.
